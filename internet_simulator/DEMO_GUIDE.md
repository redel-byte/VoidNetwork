# Internet Simulator Platform - Usage Guide

## 🚀 Quick Start

The Internet Simulator is now fully implemented with all core features working! Here's how to run the demo:

### 1. Start the Router
Open Terminal 1:
```bash
cd internet_simulator
python main.py --config configs/router.json
```

### 2. Start Client Ali
Open Terminal 2:
```bash
cd internet_simulator
python main.py --config configs/ali.json
```

### 3. Start Client Bella
Open Terminal 3:
```bash
cd internet_simulator
python main.py --config configs/bella.json
```

## 📋 Available Commands

### Message Communication
- `send_message <ip> <message> [protocol]` - Send text message
- `send_file <ip> <filename> [protocol]` - Send file

### Information Commands
- `show_status` - Show detailed node status
- `show_peers` - Show ARP and routing tables
- `show_files` - Show available files
- `show_logs` - Show recent logs
- `help_protocol` - Show protocol information

### Utility Commands
- `clear_logs` - Clear log file
- `exit` or `quit` - Exit simulator

## 🎯 Demo Scenario

### 1. Basic Message Test
In Ali's terminal:
```bash
send_message 192.168.1.3 "Hello Bella! This is Ali." tcp
```

### 2. File Transfer Test
In Ali's terminal:
```bash
send_file 192.168.1.3 notes.txt tcp
```

### 3. UDP Test (Unreliable)
In Ali's terminal:
```bash
send_message 192.168.1.3 "Quick UDP message" udp
```

## 🔍 What You'll See

### Protocol Flow
Every communication follows the complete network stack:

1. **ARP Resolution**: `[ARP] Who has 192.168.1.3?`
2. **TCP Handshake**: `[TCP] SYN → SYN-ACK → ACK`
3. **Data Transfer**: `[TCP] Sent data chunk 1/3`
4. **Routing**: `[ROUTER] Forwarding packet`
5. **Delivery**: `[TCP] Received data chunk`

### Colored Logs
- **Blue**: TCP packets
- **Yellow**: UDP packets  
- **Magenta**: ARP packets
- **Green**: Router actions

### File Transfer
- Files are fragmented into chunks
- Each chunk is numbered and tracked
- Missing chunks trigger retransmission
- Received files are saved as `received_<filename>`

## 🏗️ Architecture Features

### Implemented Protocols
- **TCP**: 3-way handshake, sequence numbers, retransmission
- **UDP**: Fast, unreliable delivery
- **ARP**: IP to MAC resolution
- **IP**: Packet routing and fragmentation

### Network Features
- **Packet Loss Simulation**: 5% for TCP, 10% for UDP
- **Routing**: Dynamic routing through gateway
- **Fragmentation**: Large files split into packets
- **Reassembly**: Received chunks reconstructed

### Educational Value
- **Real-time Logs**: See every protocol step
- **Interactive CLI**: Control network behavior
- **Multiple Nodes**: Simulate real network topology
- **File Transfer**: Test reliability vs speed

## 📁 Project Structure

```
internet_simulator/
├── configs/           # Node configurations
│   ├── router.json    # Router configuration
│   ├── ali.json       # Client Ali
│   └── bella.json     # Client Bella
├── core/              # Core simulation classes
├── protocols/         # Protocol implementations
├── utils/             # Helper utilities
├── logs/              # Generated log files
├── notes.txt          # Demo text file
├── image.png          # Demo image file
└── main.py            # Entry point
```

## 🧪 Testing Tips

### Check Network Status
```bash
show_status
show_peers
```

### Monitor Logs
```bash
show_logs
```

### Test Different Protocols
```bash
# Reliable file transfer
send_file 192.168.1.3 image.png tcp

# Fast but unreliable message
send_message 192.168.1.3 "Quick test" udp
```

### Verify File Reception
Check the `internet_simulator` directory for `received_*` files.

## 🎓 Learning Objectives

Students will observe:
1. **TCP Reliability**: How TCP ensures delivery
2. **UDP Speed**: How UDP prioritizes speed over reliability
3. **ARP Resolution**: How IP addresses map to MAC addresses
4. **Packet Routing**: How packets traverse the network
5. **Fragmentation**: How large data is split and reassembled
6. **Error Handling**: How lost packets are detected and resent

## 🔧 Advanced Features

The simulator supports:
- Multiple network topologies
- Custom packet loss rates
- Different MTU sizes
- Protocol comparison
- Network performance analysis

## 📊 Expected Output

When running the demo, you'll see detailed logs like:
```
2025-03-25 14:23:01,123 - Ali - INFO - [ARP] Sending request: Who has 192.168.1.3?
2025-03-25 14:23:01,234 - Ali - INFO - [ARP] Received reply: 192.168.1.3 -> mac-192-168-1-3
2025-03-25 14:23:01,345 - Ali - INFO - [TCP] SYN sent to 192.168.1.3:5000 (seq=12345)
2025-03-25 14:23:01,456 - Bella - INFO - [TCP] SYN received from 192.168.1.2
2025-03-25 14:23:01,567 - Router1 - INFO - [ROUTER] Forwarding packet: 192.168.1.2 -> 192.168.1.3
```

This demonstrates the complete network stack in action!

---

**🎉 The Internet Simulator is ready for your classroom demo!**
