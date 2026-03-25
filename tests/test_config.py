from pathlib import Path

from internet_sim.config import ConfigLoader


def test_config_load_save(tmp_path: Path):
    p = tmp_path / "identity.json"
    p.write_text('{"name":"A","ip":"1.1.1.1","role":"client","port":5000,"files":[]}', encoding="utf-8")
    loader = ConfigLoader(p)
    identity = loader.load()
    identity.name = "B"
    loader.save(identity)
    reloaded = loader.load()
    assert reloaded.name == "B"
