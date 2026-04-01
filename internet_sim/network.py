from __future__ import annotations

import argparse
import base64
import json
import socket
import threading
import time
from collections import defaultdict
from pathlib import Path

from .config import Identity
from .packet import Packet, fragment_payload, reassemble_payload
from .protocols import (
    SimulationControls,
    checksum_ok,
    emulate_delay,
    maybe_drop,
    missing_fragments,
    resolve_arp,
    resolve_dns,
    tcp_handshake,
)


class Node:
    def __init__(
        self,
        identity: Identity,
        logger,
        topology_path: str | Path = "config/network.json",
        controls: SimulationControls | None = None,
    ):
        self.identity = identity
        self.log = logger
        self.controls = controls or SimulationControls()
        self.topology_path = Path(topology_path)
        self.topology = json.loads(self.topology_path.read_text(encoding="utf-8"))
        self.peers = self.topology["peers"]
        self.dns_table = self.topology.get("dns", {})
        self.arp_table: dict[str, str] = {}
        self.running = False
        self.file_reassembly: dict[str, dict[int, Packet]] = defaultdict(dict)
        self.expected_counts: dict[str, int] = {}
        self.next_sequence = 1

    def start(self) -> None:
        self.running = True
        threading.Thread(target=self._udp_listener, daemon=True).start()
        threading.Thread(target=self._tcp_listener, daemon=True).start()
        self.log.info(
            f"[NODE] {self.identity.name} online at {self.identity.ip}:{self.identity.port} role={self.identity.role}"
        )

    def stop(self) -> None:
        self.running = False

    def show_peers(self) -> None:
        for ip, meta in self.peers.items():
            self.log.info(f"[PEER] {meta['name']} ip={ip} port={meta['port']} role={meta['role']}")

    def send_message(self, target: str, message: str, transport: str = "tcp") -> None:
        payload = {
            "type": "message",
            "sender": self.identity.name,
            "text": message,
            "timestamp": time.time(),
        }
        self._send_payload(target, payload, transport)

    def send_file(self, target: str, path: str, transport: str = "tcp") -> None:
        p = Path(path)
        data = p.read_bytes()
        payload = {
            "type": "file",
            "sender": self.identity.name,
            "filename": p.name,
            "content_b64": base64.b64encode(data).decode("ascii"),
            "timestamp": time.time(),
        }
        self._send_payload(target, payload, transport, packet_type="file")

    def send_http_get(self, target: str, resource: str = "/") -> None:
        payload = {
            "type": "http_request",
            "method": "GET",
            "resource": resource,
            "sender": self.identity.name,
            "timestamp": time.time(),
        }
        self._send_payload(target, payload, "tcp", packet_type="http")

    def _send_payload(
        self,
        target: str,
        payload: dict,
        transport: str,
        packet_type: str = "data",
    ) -> None:
        destination_ip = resolve_dns(target, self.dns_table, self.log)
        resolve_arp(destination_ip, self.arp_table, self.log)

        destination = self.peers[destination_ip]
        next_hop_ip = destination.get("next_hop", destination_ip)
        next_hop = self.peers[next_hop_ip]

        data = json.dumps(payload).encode("utf-8")
        packets = fragment_payload(
            self.identity.ip,
            destination_ip,
            transport.upper(),
            data,
            self.next_sequence,
            mtu=350,
            packet_type=packet_type,
        )
        self.next_sequence += len(packets)

        if transport.lower() == "udp":
            self._send_udp_packets(next_hop_ip, next_hop["port"], packets)
        else:
            self._send_tcp_packets(next_hop_ip, next_hop["port"], packets)

    def _send_udp_packets(self, ip: str, port: int, packets: list[Packet]) -> None:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        for packet in packets:
            emulate_delay(self.controls)
            if maybe_drop(packet, self.controls):
                self.log.info(
                    f"[UDP] Dropped seq={packet.sequence_number} frag={packet.fragment_id}/{packet.total_fragments}"
                )
                continue
            sock.sendto(packet.encode(), ("127.0.0.1", port))
            self.log.info(
                f"[UDP] Sent seq={packet.sequence_number} frag={packet.fragment_id}/{packet.total_fragments} to {ip}:{port}"
            )

    def _send_tcp_packets(self, ip: str, port: int, packets: list[Packet]) -> None:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        tcp_handshake(sock, ("127.0.0.1", port), self.log)
        with sock:
            for packet in packets:
                retries = 0
                while retries <= self.controls.tcp_retries:
                    emulate_delay(self.controls)
                    if maybe_drop(packet, self.controls):
                        self.log.info(
                            f"[TCP] Simulated loss seq={packet.sequence_number} frag={packet.fragment_id}/{packet.total_fragments}"
                        )
                    else:
                        sock.sendall(packet.encode() + b"\n")
                        self.log.info(
                            f"[TCP] Sent seq={packet.sequence_number} frag={packet.fragment_id}/{packet.total_fragments}"
                        )
                    sock.settimeout(0.8)
                    try:
                        ack_raw = sock.recv(4096)
                        if not ack_raw:
                            raise socket.timeout
                        ack = Packet.decode(ack_raw.strip())
                        if ack.packet_type == "ack" and ack.sequence_number == packet.sequence_number:
                            self.log.info(f"[TCP] ACK received for seq={packet.sequence_number}")
                            break
                    except (socket.timeout, ValueError):
                        retries += 1
                        self.log.info(
                            f"[TCP] Retransmit seq={packet.sequence_number} attempt={retries}/{self.controls.tcp_retries}"
                        )
                else:
                    self.log.info(f"[TCP] Failed to deliver seq={packet.sequence_number}")

    def _udp_listener(self) -> None:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.bind(("127.0.0.1", self.identity.port))
        while self.running:
            raw, addr = sock.recvfrom(65535)
            try:
                packet = Packet.decode(raw)
                self._handle_packet(packet, transport="udp", source_addr=addr, udp_socket=sock)
            except Exception as exc:  # noqa: BLE001
                self.log.info(f"[UDP] decode error: {exc}")

    def _tcp_listener(self) -> None:
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind(("127.0.0.1", self.identity.port))
        server.listen(5)
        while self.running:
            conn, addr = server.accept()
            threading.Thread(target=self._handle_tcp_connection, args=(conn, addr), daemon=True).start()

    def _handle_tcp_connection(self, conn: socket.socket, addr) -> None:
        with conn:
            buf = b""
            while self.running:
                data = conn.recv(4096)
                if not data:
                    return
                buf += data
                while b"\n" in buf:
                    line, buf = buf.split(b"\n", 1)
                    packet = Packet.decode(line)
                    self._handle_packet(packet, transport="tcp", source_addr=addr, tcp_conn=conn)

    def _handle_packet(
        self,
        packet: Packet,
        transport: str,
        source_addr,
        tcp_conn: socket.socket | None = None,
        udp_socket: socket.socket | None = None,
    ) -> None:
        if self.identity.role == "router" and packet.destination_ip != self.identity.ip:
            self._forward_packet(packet, transport)
            return

        if packet.destination_ip != self.identity.ip:
            self.log.info(
                f"[DROP] Packet for {packet.destination_ip} reached {self.identity.ip}, dropping"
            )
            return

        if not checksum_ok(packet):
            self.log.info(f"[ERROR] checksum mismatch seq={packet.sequence_number}")
            return

        key = f"{packet.source_ip}:{packet.sequence_number - packet.fragment_id + 1}:{packet.packet_type}"
        self.file_reassembly[key][packet.fragment_id] = packet
        self.expected_counts[key] = packet.total_fragments
        self.log.info(f"[CLIENT] Received chunk {packet.fragment_id}/{packet.total_fragments}")

        if transport == "tcp" and tcp_conn:
            ack = Packet(
                source_ip=self.identity.ip,
                destination_ip=packet.source_ip,
                protocol="TCP",
                payload="",
                sequence_number=packet.sequence_number,
                packet_type="ack",
            ).finalize()
            tcp_conn.sendall(ack.encode())

        if len(self.file_reassembly[key]) == self.expected_counts[key]:
            ordered = list(self.file_reassembly[key].values())
            payload_bytes = reassemble_payload(ordered)
            self._deliver_payload(packet.source_ip, payload_bytes)
            self.file_reassembly.pop(key, None)
            self.expected_counts.pop(key, None)

    def _deliver_payload(self, source_ip: str, payload_bytes: bytes) -> None:
        msg = json.loads(payload_bytes.decode("utf-8"))
        if msg["type"] == "message":
            self.log.info(f"[APP] Message from {msg['sender']} ({source_ip}): {msg['text']}")
            return

        if msg["type"] == "file":
            out_dir = Path("received")
            out_dir.mkdir(exist_ok=True)
            out_path = out_dir / msg["filename"]
            out_path.write_bytes(base64.b64decode(msg["content_b64"]))
            self.log.info(
                f"[APP] File from {msg['sender']} ({source_ip}) stored at {out_path.as_posix()}"
            )
            return

        if msg["type"] == "http_request":
            self.log.info(
                f"[HTTP] {msg['method']} {msg['resource']} from {msg['sender']} ({source_ip})"
            )
            body = f"Hello from {self.identity.name}. You requested {msg['resource']}"
            response = {
                "type": "http_response",
                "status": 200,
                "body": body,
                "sender": self.identity.name,
                "timestamp": time.time(),
            }
            self._send_payload(source_ip, response, "tcp", packet_type="http")
            return

        if msg["type"] == "http_response":
            self.log.info(
                f"[HTTP] Response {msg['status']} from {msg['sender']} ({source_ip}): {msg['body']}"
            )

    def _forward_packet(self, packet: Packet, transport: str) -> None:
        destination = self.peers[packet.destination_ip]
        next_hop_ip = destination.get("next_hop", packet.destination_ip)
        next_hop = self.peers[next_hop_ip]
        self.log.info(
            f"[ROUTER] Forwarding seq={packet.sequence_number} to {next_hop_ip}:{next_hop['port']}"
        )
        if transport == "udp":
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.sendto(packet.encode(), ("127.0.0.1", next_hop["port"]))
        else:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.connect(("127.0.0.1", next_hop["port"]))
                sock.sendall(packet.encode() + b"\n")


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    parser.add_argument("--topology", default="config/network.json")
    parser.add_argument("--loss", type=float, default=0.2)
    return parser
