from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, asdict


@dataclass
class Packet:
    source_ip: str
    destination_ip: str
    protocol: str
    payload: str
    sequence_number: int = 0
    fragment_id: int = 0
    total_fragments: int = 1
    checksum: str = ""
    packet_type: str = "data"

    def finalize(self) -> "Packet":
        self.checksum = self.compute_checksum()
        return self

    def compute_checksum(self) -> str:
        digest = hashlib.sha256(
            f"{self.source_ip}|{self.destination_ip}|{self.protocol}|"
            f"{self.sequence_number}|{self.fragment_id}|{self.total_fragments}|{self.payload}".encode("utf-8")
        ).hexdigest()
        return digest[:16]

    def is_valid(self) -> bool:
        return self.checksum == self.compute_checksum()

    def encode(self) -> bytes:
        return json.dumps(asdict(self)).encode("utf-8")

    @classmethod
    def decode(cls, raw: bytes) -> "Packet":
        data = json.loads(raw.decode("utf-8"))
        return cls(**data)


def fragment_payload(
    source_ip: str,
    destination_ip: str,
    protocol: str,
    payload: bytes,
    sequence_start: int,
    mtu: int = 512,
    packet_type: str = "data",
) -> list[Packet]:
    chunks = [payload[i : i + mtu] for i in range(0, len(payload), mtu)] or [b""]
    packets = []
    for idx, chunk in enumerate(chunks, start=1):
        packets.append(
            Packet(
                source_ip=source_ip,
                destination_ip=destination_ip,
                protocol=protocol,
                payload=chunk.hex(),
                sequence_number=sequence_start + idx - 1,
                fragment_id=idx,
                total_fragments=len(chunks),
                packet_type=packet_type,
            ).finalize()
        )
    return packets


def reassemble_payload(packets: list[Packet]) -> bytes:
    ordered = sorted(packets, key=lambda p: p.fragment_id)
    return b"".join(bytes.fromhex(packet.payload) for packet in ordered)
