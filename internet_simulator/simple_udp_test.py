#!/usr/bin/env python3
"""
Simple UDP test without port parsing issues
"""

import threading
import time
from utils.config_loader import load_config
from core.client import Client
from main import register_node

def simple_udp_test():
    print("=== Simple UDP Test ===")
    
    # Create two clients
    config1 = load_config('configs/user.json')
    config2 = load_config('configs/ali.json')
    
    # Use different ports to avoid conflicts
    config1['port'] = 5000
    config2['port'] = 5005
    
    client1 = Client(config1)
    client2 = Client(config2)
    
    # Register both nodes
    register_node(config1['ip'], '127.0.0.1', client1.port)
    register_node(config2['ip'], '127.0.0.1', client2.port)
    
    print(f"Client1: {client1.name} ({client1.ip}:{client1.port})")
    print(f"Client2: {client2.name} ({client2.ip}:{client2.port})")
    
    # Wait for setup
    time.sleep(1)
    
    # Test 1: Direct message
    print(f"\n=== Test 1: Direct UDP Message ===")
    print("Sending: 'Hello Ali!' from User to Ali")
    
    # Create a simple UDP packet without port complications
    from core.packet import Packet
    message_data = b"MESSAGE:Hello Ali!"
    packet = client1.create_packet(client2.ip, 'udp', message_data)
    
    # Send directly
    success = client1.send_packet(packet, client2.ip)
    print(f"Send result: {success}")
    
    # Wait for processing
    time.sleep(2)
    
    # Check what was received
    print(f"Client2 receive buffer length: {len(client2.udp_manager.default_socket.receive_buffer)}")
    if client2.udp_manager.default_socket.receive_buffer:
        data, src_ip = client2.udp_manager.default_socket.receive_buffer[0]
        try:
            message = data.decode()
            print(f"Received message: '{message}'")
            if message.startswith("MESSAGE:"):
                content = message[9:]  # Remove "MESSAGE:" prefix
                print(f"DISPLAY MESSAGE: [Message from {src_ip}]: {content}")
        except:
            print(f"Raw data: {data}")
    
    # Test 2: Send multiple messages
    print(f"\n=== Test 2: Multiple Messages ===")
    
    messages = [
        "Hi Ali!",
        "How are you?",
        "This is a test"
    ]
    
    for i, msg in enumerate(messages):
        print(f"Sending message {i+1}: '{msg}'")
        message_data = f"MESSAGE:{msg}".encode()
        packet = client1.create_packet(client2.ip, 'udp', message_data)
        client1.send_packet(packet, client2.ip)
        time.sleep(1)
        
        # Check if received
        if client2.udp_manager.default_socket.receive_buffer:
            data, src_ip = client2.udp_manager.default_socket.receive_buffer[-1]
            try:
                received_msg = data.decode()
                if received_msg.startswith("MESSAGE:"):
                    content = received_msg[9:]
                    print(f"✅ Received: [Message from {src_ip}]: {content}")
                else:
                    print(f"❌ Unexpected format: {received_msg}")
            except:
                print(f"❌ Decode error: {data}")
        else:
            print(f"❌ No message received")
    
    # Cleanup
    client1.running = False
    client2.running = False
    print(f"\n=== Test Complete ===")

if __name__ == "__main__":
    simple_udp_test()
