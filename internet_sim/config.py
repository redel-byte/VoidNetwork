from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from pathlib import Path


@dataclass
class Identity:
    name: str
    ip: str
    role: str
    port: int
    files: list[str] = field(default_factory=list)

    def update(self, **kwargs: object) -> None:
        for key, value in kwargs.items():
            if value is not None and hasattr(self, key):
                setattr(self, key, value)


class ConfigLoader:
    def __init__(self, path: str | Path):
        self.path = Path(path)

    def load(self) -> Identity:
        data = json.loads(self.path.read_text(encoding="utf-8"))
        return Identity(**data)

    def save(self, identity: Identity) -> None:
        self.path.write_text(
            json.dumps(asdict(identity), indent=2),
            encoding="utf-8",
        )
