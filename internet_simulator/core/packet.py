import hashlib
import struct
import time

class Packet:
    """Simulated IP packet with fragmentation support."""
    MAX_PAYLOAD = 1024  # bytes (to simulate MTU)

    def __init__(self, src_ip, dst_ip, protocol, payload, seq=0, frag_offset=0, more_frags=False):
        self.src_ip = src_ip
        self.dst_ip = dst_ip
        self.protocol = protocol  # 'tcp' or 'udp'
        self.payload = payload    # bytes
        self.seq = seq            # sequence number for reassembly
        self.frag_offset = frag_offset
        self.more_frags = more_frags
        self.checksum = self.calc_checksum()

    def calc_checksum(self):
        """Simple checksum (MD5 of header + payload)."""
        data = f"{self.src_ip}{self.dst_ip}{self.protocol}{self.seq}{self.frag_offset}{self.more_frags}".encode()
        data += self.payload
        return hashlib.md5(data).hexdigest()[:8]

    def is_valid(self):
        """Verify checksum."""
        return self.calc_checksum() == self.checksum

    def to_bytes(self):
        """Serialize packet to bytes for transmission."""
        # Use a simple delimiter-based format for robustness
        parts = [
            self.src_ip,
            self.dst_ip,
            self.protocol,
            str(self.seq),
            str(self.frag_offset),
            str(int(self.more_frags)),
            self.checksum
        ]
        header = '|'.join(parts).encode() + b'|'
        return header + self.payload

    @classmethod
    def from_bytes(cls, data):
        """Deserialize from bytes."""
        # Find the end of header (double delimiter)
        header_end = data.find(b'||')
        if header_end == -1:
            raise ValueError("Invalid packet format")
        
        header_data = data[:header_end]
        payload = data[header_end + 2:]  # Skip the double delimiter
        
        parts = header_data.decode().split('|')
        if len(parts) != 7:
            raise ValueError("Invalid packet header format")
        
        src_ip = parts[0]
        dst_ip = parts[1]
        protocol = parts[2]
        seq = int(parts[3])
        frag_offset = int(parts[4])
        more_frags = bool(int(parts[5]))
        checksum = parts[6]
        
        packet = cls(src_ip, dst_ip, protocol, payload, seq, frag_offset, more_frags)
        packet.checksum = checksum
        return packet