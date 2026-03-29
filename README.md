# Interactive Internet Simulator (Classroom Edition)

This project is an educational, interactive simulator that lets each student run a network node and observe packet flow through DNS, ARP, routing, transport, and application layers.

## Quick start

```bash
python -m internet_sim.cli --config config/student_a.json
```

Open another terminal for student B and router.

## Commands

- `send_message --to <ip|domain> --message "..." [--transport tcp|udp]`
- `send_file --to <ip|domain> --path <file> [--transport tcp|udp]`
- `chat --to <ip|domain> [--transport tcp|udp]`
- `show_peers`
- `show_logs [--tail N]`
- `set_identity --name NAME --ip IP --port PORT --role ROLE`
- `exit`

## Demo scenario

Use the supplied configs under `config/` and run:

- Router: `python -m internet_sim.cli --config config/router_1.json`
- Student B: `python -m internet_sim.cli --config config/student_b.json`
- Student A: `python -m internet_sim.cli --config config/student_a.json`

From A, run:

```bash
send_message --to 192.168.1.3 --message "Hello from A" --transport tcp
send_file --to 192.168.1.3 --path examples/class_photo.txt --transport tcp
```

Logs will show DNS/ARP lookups, 3-way handshake, routed forwarding, simulated packet loss, retransmission, and file reassembly.
