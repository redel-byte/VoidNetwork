import json
from pathlib import Path

from internet_sim.config import Identity
from internet_sim.network import Node


class NullLogger:
    def info(self, *_args, **_kwargs):
        return None


def test_router_next_hop_self_loop_prevented(tmp_path: Path):
    topology = {
        "dns": {},
        "peers": {
            "192.168.1.2": {"name": "Ali", "role": "client", "port": 5001, "next_hop": "10.0.0.1"},
            "192.168.1.3": {"name": "Sara", "role": "server", "port": 5002, "next_hop": "10.0.0.1"},
            "10.0.0.1": {"name": "R1", "role": "router", "port": 5000},
        },
    }
    topo_file = tmp_path / "topology.json"
    topo_file.write_text(json.dumps(topology), encoding="utf-8")

    router = Node(
        identity=Identity(name="R1", ip="10.0.0.1", role="router", port=5000, files=[]),
        logger=NullLogger(),
        topology_path=topo_file,
    )

    assert router._resolve_next_hop("192.168.1.3") == "192.168.1.3"
