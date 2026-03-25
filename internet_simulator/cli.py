import cmd
import threading
import os
from core.client import Client
from core.router import Router

class NodeCLI(cmd.Cmd):
    intro = "Welcome to the Internet Simulator. Type help or ? to list commands.\n"
    prompt = "(sim) "

    def __init__(self, node):
        super().__init__()
        self.node = node

    def do_send_message(self, arg):
        "Send a message: send_message <ip> <message> [protocol]"
        parts = arg.split(maxsplit=2)
        if len(parts) < 2:
            print("Usage: send_message <ip> <message> [protocol]")
            return
        
        ip = parts[0]
        message = parts[1]
        protocol = parts[2] if len(parts) > 2 else 'tcp'
        
        self.node.send_message(ip, message, protocol)

    def do_send_file(self, arg):
        "Send a file: send_file <ip> <filename> [protocol]"
        parts = arg.split(maxsplit=2)
        if len(parts) < 2:
            print("Usage: send_file <ip> <filename> [protocol]")
            return
        
        ip, filename = parts[0], parts[1]
        protocol = parts[2] if len(parts) > 2 else 'tcp'
        
        self.node.send_file(ip, filename, protocol)

    def do_show_peers(self, arg):
        "Show known peers (ARP table, routing table, etc.)"
        print("\n=== Network Information ===")
        
        # Show ARP table
        arp_info = self.node.arp_table.show_table()
        print(arp_info)
        
        # Show routing table
        print(f"\nRouting Table:")
        if self.node.routing_table.routes:
            for route in self.node.routing_table.routes:
                print(f"  {route[0]}/{route[1]} via {route[2]}")
        else:
            print("  No routes configured")

    def do_show_status(self, arg):
        "Show detailed node status"
        if hasattr(self.node, 'show_status'):
            self.node.show_status()
        else:
            print(f"\n=== {self.node.name} Status ===")
            print(f"IP: {self.node.ip}")
            print(f"Port: {self.node.port}")
            print(f"Role: {self.node.config.get('role', 'unknown')}")
            print(f"Default Gateway: {self.node.default_gateway or 'None'}")

    def do_show_files(self, arg):
        "Show available files for sending"
        if hasattr(self.node, 'show_files'):
            self.node.show_files()
        else:
            files = self.node.config.get('files', [])
            print(f"\nAvailable files for {self.node.name}:")
            for filename in files:
                if os.path.exists(filename):
                    size = os.path.getsize(filename)
                    print(f"  - {filename} ({size} bytes)")
                else:
                    print(f"  - {filename} (file not found)")

    def do_show_logs(self, arg):
        "Show recent logs (prints last 20 lines of log file)"
        try:
            log_file = f"logs/{self.node.name}.log"
            if os.path.exists(log_file):
                with open(log_file, 'r') as f:
                    lines = f.readlines()
                    # Show last 20 lines
                    recent_lines = lines[-20:] if len(lines) > 20 else lines
                    print(f"\n=== Recent Logs for {self.node.name} ===")
                    for line in recent_lines:
                        print(line.rstrip())
            else:
                print(f"No log file found for {self.node.name}")
        except Exception as e:
            print(f"Error reading log file: {e}")

    def do_clear_logs(self, arg):
        "Clear the log file for this node"
        try:
            log_file = f"logs/{self.node.name}.log"
            if os.path.exists(log_file):
                open(log_file, 'w').close()
                print(f"Log file for {self.node.name} cleared")
            else:
                print(f"No log file found for {self.node.name}")
        except Exception as e:
            print(f"Error clearing log file: {e}")

    def do_help_protocol(self, arg):
        "Show information about available protocols"
        print("\n=== Protocol Information ===")
        print("TCP - Transmission Control Protocol")
        print("  - Reliable delivery with 3-way handshake")
        print("  - Sequence numbers and acknowledgments")
        print("  - Automatic retransmission of lost packets")
        print("  - Recommended for file transfers and important messages")
        print()
        print("UDP - User Datagram Protocol")
        print("  - Fast, connectionless communication")
        print("  - No guarantee of delivery or order")
        print("  - Lower overhead than TCP")
        print("  - Good for real-time data where speed is more important than reliability")
        print()
        print("ARP - Address Resolution Protocol")
        print("  - Resolves IP addresses to MAC addresses")
        print("  - Used automatically before sending packets")
        print()
        print("Usage examples:")
        print("  send_message 192.168.1.3 \"Hello!\" tcp")
        print("  send_file 192.168.1.3 image.png tcp")
        print("  send_message 192.168.1.3 \"Quick message\" udp")

    def do_exit(self, arg):
        "Exit the simulator"
        print(f"Shutting down {self.node.name}...")
        self.node.running = False
        return True

    def do_quit(self, arg):
        "Exit the simulator"
        return self.do_exit(arg)

    def default(self, line):
        if line:
            print(f"Unknown command: {line}")
            print("Type 'help' for available commands")