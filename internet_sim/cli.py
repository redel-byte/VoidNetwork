from __future__ import annotations

import shlex
from pathlib import Path

from .config import ConfigLoader
from .logging_utils import setup_logger
from .network import Node, build_arg_parser
from .protocols import SimulationControls


def print_help() -> None:
    print(
        """
Commands:
  send_message --to <ip|domain> --message "text" [--transport tcp|udp]
  send_file --to <ip|domain> --path <file> [--transport tcp|udp]
  chat --to <ip|domain> [--transport tcp|udp]
  http_get --to <ip|domain> [--resource /path]
  show_peers
  show_logs [--tail N]
  set_identity --name N --ip IP --port P --role ROLE
  help
  exit
"""
    )


def parse_flag(tokens: list[str], name: str, default: str | None = None) -> str | None:
    if name not in tokens:
        return default
    idx = tokens.index(name)
    if idx + 1 >= len(tokens):
        return default
    return tokens[idx + 1]


def run_cli() -> None:
    args = build_arg_parser().parse_args()

    loader = ConfigLoader(args.config)
    identity = loader.load()
    logger = setup_logger(identity.name)

    node = Node(
        identity=identity,
        logger=logger,
        topology_path=args.topology,
        controls=SimulationControls(packet_loss_rate=args.loss),
    )
    node.start()

    print_help()

    while True:
        try:
            raw = input(f"{identity.name}@{identity.ip}> ").strip()
        except EOFError:
            break
        if not raw:
            continue

        tokens = shlex.split(raw)
        cmd = tokens[0]

        if cmd == "exit":
            break
        if cmd == "help":
            print_help()
            continue
        if cmd == "show_peers":
            node.show_peers()
            continue
        if cmd == "show_logs":
            tail = int(parse_flag(tokens, "--tail", "20"))
            log_file = Path("logs") / f"{identity.name}.log"
            if log_file.exists():
                lines = log_file.read_text(encoding="utf-8").splitlines()[-tail:]
                for line in lines:
                    print(line)
            continue
        if cmd == "send_message":
            node.send_message(
                parse_flag(tokens, "--to") or "",
                parse_flag(tokens, "--message") or "",
                parse_flag(tokens, "--transport", "tcp") or "tcp",
            )
            continue
        if cmd == "send_file":
            node.send_file(
                parse_flag(tokens, "--to") or "",
                parse_flag(tokens, "--path") or "",
                parse_flag(tokens, "--transport", "tcp") or "tcp",
            )
            continue
        if cmd == "chat":
            target = parse_flag(tokens, "--to") or ""
            transport = parse_flag(tokens, "--transport", "tcp") or "tcp"
            print("Enter chat mode. Type '/quit' to exit.")
            while True:
                msg = input("chat> ")
                if msg.strip() == "/quit":
                    break
                node.send_message(target, msg, transport)
            continue
        if cmd == "http_get":
            node.send_http_get(
                parse_flag(tokens, "--to") or "",
                parse_flag(tokens, "--resource", "/") or "/",
            )
            continue
        if cmd == "set_identity":
            identity.update(
                name=parse_flag(tokens, "--name"),
                ip=parse_flag(tokens, "--ip"),
                port=int(parse_flag(tokens, "--port", str(identity.port))),
                role=parse_flag(tokens, "--role"),
            )
            loader.save(identity)
            print("Identity updated and saved.")
            continue

        print("Unknown command. Type 'help'.")

    node.stop()


if __name__ == "__main__":
    run_cli()
