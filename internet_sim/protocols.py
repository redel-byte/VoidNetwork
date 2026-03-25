from __future__ import annotations

import random
import socket
import time
from dataclasses import dataclass
from typing import Iterable

from .packet import Packet


@dataclass
class SimulationControls:
    packet_loss_rate: float = 0.2
    min_delay_s: float = 0.01
    max_delay_s: float = 0.05
    tcp_retries: int = 3


def resolve_dns(target: str, dns_table: dict[str, str], log) -> str:
    if _looks_like_ip(target):
        return target
    ip = dns_table.get(target)
    if not ip:
        raise ValueError(f"Domain '{target}' not found in DNS table")
    log.info(f"[DNS] Resolving {target} -> {ip}")
    return ip


def resolve_arp(target_ip: str, arp_table: dict[str, str], log) -> str:
    if target_ip not in arp_table:
        log.info(f"[ARP] Who has {target_ip}? (simulated broadcast)")
        arp_table[target_ip] = "aa:bb:cc:dd:ee:ff"
    mac = arp_table[target_ip]
    log.info(f"[ARP] {target_ip} is-at {mac}")
    return mac


def tcp_handshake(sock: socket.socket, destination: tuple[str, int], log) -> None:
    log.info("[TCP] SYN ->")
    sock.connect(destination)
    log.info("[TCP] <- SYN-ACK")
    log.info("[TCP] ACK ->")


def maybe_drop(packet: Packet, controls: SimulationControls) -> bool:
    if packet.packet_type in {"ack", "syn", "synack", "handshake"}:
        return False
    return random.random() < controls.packet_loss_rate


def emulate_delay(controls: SimulationControls) -> None:
    time.sleep(random.uniform(controls.min_delay_s, controls.max_delay_s))


def checksum_ok(packet: Packet) -> bool:
    return packet.is_valid()


def _looks_like_ip(value: str) -> bool:
    parts = value.split(".")
    if len(parts) != 4:
        return False
    try:
        return all(0 <= int(part) <= 255 for part in parts)
    except ValueError:
        return False


def missing_fragments(received: Iterable[int], total: int) -> list[int]:
    seen = set(received)
    return [i for i in range(1, total + 1) if i not in seen]
