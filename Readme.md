```markdown
# Internet Simulator Platform

An interactive, educational simulation of core Internet protocols (ARP, IP, TCP, UDP, routing) designed for a classroom of junior developers. Students can run their own nodes (clients, routers) with custom identities, communicate via messages and file transfers, and observe the complete data flow from DNS/ARP resolution to packet fragmentation, retransmission, and reassembly.

## Features

- **User Identity System** – Each node loads a JSON config with name, IP, role, and files.
- **Communication** – Send text messages and files (images, text, etc.) between clients.
- **Protocol Simulation** – Realistic simulation of:
  - **ARP** (request/reply)
  - **IP** (packet structure, routing)
  - **TCP** (3-way handshake, sequence numbers, retransmission)
  - **UDP** (unreliable, fast)
  - **HTTP** (basic request/response, DNS resolution)
- **Network Flow** – Every communication follows: DNS → ARP → TCP/UDP → routing → delivery.
- **Packet Handling** – Fragmentation, reassembly, packet loss simulation, delay simulation.
- **Logging & Observability** – Human-readable, timestamped logs showing each protocol action.
- **Interactive CLI** – Commands to send messages/files, show peers, view logs.
- **Extensible** – Modular design to add firewalls, VPN, proxy, etc.

## Requirements

- Python 3.7 or higher
- No external dependencies (uses only standard library)

## Installation

1. Clone or download the project:
   ```bash
   git clone https://github.com/yourusername/internet-simulator.git
   cd internet-simulator
   ```
2. (Optional) Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate   # On Windows: venv\Scripts\activate
   ```

## Configuration

Each node requires a JSON configuration file. Place them in the `configs/` folder.

Example `configs/ali.json`:
```json
{
  "name": "Ali",
  "ip": "192.168.1.2",
  "role": "client",
  "port": 5002,
  "files": ["image.png", "notes.txt"],
  "default_gateway": "192.168.1.1"
}
```

- `name` – Student name (appears in logs).
- `ip` – Static IP address for this node.
- `role` – `client` or `router`.
- `port` – UDP port the node listens on (must be unique per node).
- `files` – List of file names that the node can send (files must exist in the node’s current directory).
- `default_gateway` – (optional) Used for routing; usually the router’s IP.

For a router node:
```json
{
  "name": "Router1",
  "ip": "192.168.1.1",
  "role": "router",
  "port": 5001
}
```

## Running the Simulator

Open one terminal per node.

**Router** (must be started first so clients can resolve it):
```bash
python main.py --config configs/router.json
```

**Client 1** (Ali):
```bash
python main.py --config configs/ali.json
```

**Client 2** (Bella):
```bash
python main.py --config configs/bella.json
```

Each terminal opens an interactive CLI. Type `help` to see available commands.

## Commands

| Command | Description |
|---------|-------------|
| `send_message <ip> <message>` | Send a text message to another node. |
| `send_file <ip> <filename>` | Send a file (from the node’s `files` list) to another node. |
| `show_peers` | Display ARP table and routing table. |
| `show_logs` | Show the last lines of the node’s log file. |
| `exit` | Stop the node. |

## Demo Scenario

1. Start the router and both clients as described above.
2. In Ali’s CLI, send a message to Bella:
   ```
   send_message 192.168.1.3 "Hello Bella!"
   ```
   - The simulator will perform ARP to find Bella’s MAC, then TCP handshake, then deliver the message.
   - Logs show each step: `[ARP]`, `[TCP]`, `[ROUTER]`, etc.
3. Send a file (e.g., `image.png`) from Ali to Bella:
   ```
   send_file 192.168.1.3 image.png
   ```
   - The file is split into packets (fragmentation), sent over TCP, and reassembled.
   - Packet loss (5%) triggers TCP retransmission – visible in logs.
4. Bella receives the file and saves it as `received_image.png` in its working directory.

## Logging & Observability

Each node writes logs to `logs/<name>.log` and also prints them to the console with timestamps. Example:
```
2025-03-25 14:23:01,123 - Ali - INFO - [ARP] Sending ARP request for 192.168.1.3
2025-03-25 14:23:01,234 - Ali - INFO - [ARP] Received ARP reply from 192.168.1.3 -> mac-bella
2025-03-25 14:23:01,345 - Ali - INFO - [TCP] SYN sent to 192.168.1.3
2025-03-25 14:23:01,456 - Ali - INFO - [TCP] SYN-ACK received, connection established
```

These logs help students trace exactly what happens under the hood.

## Project Structure

```
internet-simulator/
├── configs/               # JSON configuration files
├── logs/                  # Generated log files
├── core/                  # Core simulation classes
│   ├── packet.py          # Packet structure, fragmentation
│   ├── node.py            # Base Node (network stack)
│   ├── client.py          # Client node implementation
│   ├── router.py          # Router node implementation
├── protocols/             # Protocol implementations
│   ├── arp.py             # ARP table, request/reply logic
│   ├── ip.py              # IP packet handling, routing table
│   ├── tcp.py             # TCP state machine
│   └── udp.py             # UDP handler
├── utils/                 # Helper modules
│   ├── config_loader.py   # Load and validate JSON configs
│   └── logger.py          # Colored logging to file and console
├── cli.py                 # Command-line interface using cmd
├── main.py                # Entry point
└── README.md              # This file
```

## How It Works (High‑Level)

1. **Startup** – The node loads its config, binds to a UDP port, and registers its IP in a global registry (for address resolution).
2. **Sending** – When a user issues a command, the node:
   - Checks if the destination IP is in the ARP table; if not, broadcasts an ARP request.
   - Resolves the next hop via the routing table.
   - For TCP: performs a 3‑way handshake, then sends data packets with sequence numbers and waits for ACKs.
   - For UDP: sends packets without connection setup.
3. **Routing** – Routers simply forward packets based on the destination IP (using their routing table).
4. **Receiving** – The node demultiplexes incoming packets by protocol and delivers them to the appropriate handler (TCP/UDP). TCP handles reassembly, ACKs, and retransmission.
5. **File Transfer** – Files are read in chunks, each chunk sent as a TCP segment. The receiver writes chunks to disk and reassembles them.

## Extending the Simulator

The modular design makes it easy to add new features:

- **DNS** – Add a DNS server node and modify the client to resolve domain names before sending.
- **HTTP** – Implement a simple HTTP server/client using TCP.
- **Firewall** – Extend the `Node` class to filter packets based on rules.
- **VPN** – Encapsulate packets with a simulated encryption layer.

To add a new protocol, subclass `Node` and implement a new handler in `packet_handlers`.

## License

This project is open source and available under the MIT License. Feel free to use and modify for educational purposes.

---

**Happy simulating!**
```