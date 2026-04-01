from internet_sim.packet import Packet, fragment_payload, reassemble_payload


def test_packet_checksum_roundtrip():
    pkt = Packet("1.1.1.1", "2.2.2.2", "TCP", "abcd", sequence_number=1).finalize()
    encoded = pkt.encode()
    decoded = Packet.decode(encoded)
    assert decoded.is_valid()


def test_fragment_and_reassemble():
    data = b"x" * 1200
    packets = fragment_payload("1.1.1.1", "2.2.2.2", "TCP", data, 1, mtu=300)
    assert len(packets) == 4
    out = reassemble_payload(packets)
    assert out == data
