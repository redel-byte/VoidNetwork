#!/usr/bin/env python3
"""
Debug UDP communication step by step
"""

import threading
import time
from utils.config_loader import load_config
from core.client import Client
from main import register_node

def debug_udp_test():
    print("=== UDP Debug Test ===")
    
    # Create two clients with different ports to avoid conflicts
    config1 = load_config('configs/user.json')
    config2 = load_config('configs/ali.json')
    
    # Modify ports to avoid conflicts
    config1['port'] = 5000
    config2['port'] = 5004  # Different port
    
    client1 = Client(config1)
    client2 = Client(config2)
    
    # Register both nodes with actual ports
    register_node(config1['ip'], '127.0.0.1', client1.port)
    register_node(config2['ip'], '127.0.0.1', client2.port)
    
    print(f"Client1: {client1.name} ({client1.ip}:{client1.port})")
    print(f"Client2: {client2.name} ({client2.ip}:{client2.port})")
    
    # Show routing tables
    print(f"\nClient1 routing table:")
    for route in client1.routing_table.routes:
        print(f"  {route[0]}/{route[1]} via {route[2]}")
    
    print(f"\nClient2 routing table:")
    for route in client2.routing_table.routes:
        print(f"  {route[0]}/{route[1]} via {route[2]}")
    
    # Test ARP resolution
    print(f"\n=== ARP Test ===")
    print(f"Client1 ARP table: {client1.arp_table.table}")
    print(f"Client2 ARP table: {client2.arp_table.table}")
    
    # Wait for setup
    time.sleep(1)
    
    # Test UDP message
    print(f"\n=== Sending Message ===")
    test_message = "Hello from User to Ali!"
    print(f"Sending: '{test_message}' from {client1.ip} to {client2.ip}")
    
    # Manually trigger ARP resolution
    print(f"Resolving {client2.ip}...")
    mac = client1.arp_table.resolve(client2.ip)
    print(f"ARP result: {mac}")
    
    # Check routing
    next_hop = client1.routing_table.get_next_hop(client2.ip)
    print(f"Next hop: {next_hop}")
    
    # Check address resolution
    address = client1.resolve_ip_to_address(next_hop)
    print(f"Address resolution: {address}")
    
    # Send message
    print(f"Sending message...")
    result = client1.send_message(client2.ip, test_message, 'udp')
    print(f"Send result: {result}")
    
    # Wait for processing
    print(f"\n=== Waiting for Message ===")
    time.sleep(3)
    
    # Check if message was received
    print(f"Client2 receive buffer: {client2.udp_manager.default_socket.receive_buffer}")
    
    # Cleanup
    client1.running = False
    client2.running = False
    print(f"\n=== Test Complete ===")

if __name__ == "__main__":
    debug_udp_test()
