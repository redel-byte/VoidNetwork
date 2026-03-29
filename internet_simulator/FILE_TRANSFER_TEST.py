#!/usr/bin/env python3
"""
File Transfer Test - Test if file sending works across networks
"""

import threading
import time
from utils.config_loader import load_config
from core.client import Client
from core.router import Router
from shared_registry import register_shared_node, get_all_shared_nodes

def file_transfer_test():
    print("=== FILE TRANSFER TEST ===")
    
    # Create test files if they don't exist
    import os
    if not os.path.exists("test_file.txt"):
        with open("test_file.txt", "w") as f:
            f.write("Hello, this is a test file for the Internet Simulator!\n")
            f.write("It contains multiple lines of text.\n")
            f.write("Line 3: Testing file transfer functionality.\n")
            f.write("Line 4: This should work across networks.\n")
    
    print("Created test_file.txt for testing")
    
    # Create router
    router_config = load_config('configs/router_dual_network.json')
    router = Router(router_config)
    register_shared_node(router_config['ip'], '127.0.0.1', router_config['port'])
    
    # Create clients on different networks
    config1 = load_config('configs/network1_client.json')
    config2 = load_config('configs/network2_client.json')
    
    # Use different ports to avoid conflicts
    config1['port'] = 5000
    config2['port'] = 5004
    
    # Add test file to client's allowed files list
    config1['files'] = ['test_file.txt'] + config1.get('files', [])
    config2['files'] = ['test_file.txt'] + config2.get('files', [])
    
    client1 = Client(config1)  # User on Network 1
    client2 = Client(config2)  # Ali on Network 2
    
    # Register clients
    register_shared_node(config1['ip'], '127.0.0.1', client1.port)
    register_shared_node(config2['ip'], '127.0.0.1', client2.port)
    
    print(f"Router: {router.name} ({router.ip}:{router.port})")
    print(f"Client1: {client1.name} ({client1.ip}:{client1.port}) - Network 1")
    print(f"Client2: {client2.name} ({client2.ip}:{client2.port}) - Network 2")
    print(f"Client1 files: {client1.files}")
    print(f"Client2 files: {client2.files}")
    
    # Wait for setup
    time.sleep(2)
    
    # Test 1: UDP file transfer (should be unreliable)
    print(f"\n=== Test 1: UDP File Transfer ===")
    print("Sending test_file.txt via UDP (may lose packets)...")
    
    try:
        result = client1.send_file(client2.ip, "test_file.txt", "udp")
        print(f"UDP send result: {result}")
        time.sleep(3)
        
        # Check for received files in current directory
        received_files = [f for f in os.listdir('.') if f.startswith('received_')]
        print(f"Received files in directory: {received_files}")
        
    except Exception as e:
        print(f"UDP file transfer error: {e}")
    
    # Test 2: TCP file transfer (should be reliable)
    print(f"\n=== Test 2: TCP File Transfer ===")
    print("Sending test_file.txt via TCP (reliable)...")
    
    try:
        result = client1.send_file(client2.ip, "test_file.txt", "tcp")
        print(f"TCP send result: {result}")
        time.sleep(5)  # Give more time for TCP handshake
        
        # Check for received files in current directory
        received_files = [f for f in os.listdir('.') if f.startswith('received_')]
        print(f"Received files in directory: {received_files}")
        
        if received_files:
            latest_file = received_files[-1]
            if os.path.exists(latest_file):
                with open(latest_file, 'r') as f:
                    content = f.read()
                print(f"File content: {content[:200]}...")
            
    except Exception as e:
        print(f"TCP file transfer error: {e}")
    
    # Test 3: Check TCP connection status
    print(f"\n=== Test 3: TCP Connection Status ===")
    print(f"Client1 connections: {list(client1.tcp_manager.connections.keys())}")
    print(f"Client2 connections: {list(client2.tcp_manager.connections.keys())}")
    
    # Test 4: Show available files
    print(f"\n=== Test 4: Available Files ===")
    client1.show_files()
    client2.show_files()
    
    # Cleanup
    router.running = False
    client1.running = False
    client2.running = False
    
    print(f"\n=== Test Complete ===")
    print("Check for files starting with 'received_' in the directory.")

if __name__ == "__main__":
    file_transfer_test()
