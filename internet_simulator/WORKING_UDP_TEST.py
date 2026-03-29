#!/usr/bin/env python3
"""
Working UDP test - bypass the port parsing issue
"""

import threading
import time
from utils.config_loader import load_config
from core.client import Client
from main import register_node

def working_udp_test():
    print("=== WORKING UDP TEST ===")
    
    # Create two clients
    config1 = load_config('configs/user.json')
    config2 = load_config('configs/ali.json')
    
    # Use different ports to avoid conflicts
    config1['port'] = 5000
    config2['port'] = 5006
    
    client1 = Client(config1)
    client2 = Client(config2)
    
    # Register both nodes
    register_node(config1['ip'], '127.0.0.1', client1.port)
    register_node(config2['ip'], '127.0.0.1', client2.port)
    
    print(f"Client1: {client1.name} ({client1.ip}:{client1.port})")
    print(f"Client2: {client2.name} ({client2.ip}:{client2.port})")
    
    # Wait for setup
    time.sleep(1)
    
    # Test: Send messages using the client's built-in method
    print(f"\n=== Sending Messages ===")
    
    messages = [
        "Hello Ali!",
        "How are you?", 
        "This is working!",
        "Final test message"
    ]
    
    for i, msg in enumerate(messages):
        print(f"\n--- Message {i+1} ---")
        print(f"Sending: '{msg}'")
        
        # Use the client's send_message method
        result = client1.send_message(client2.ip, msg, 'udp')
        print(f"Send result: {result}")
        
        # Wait for processing
        time.sleep(2)
        
        # Check what's in the receive buffer
        if client2.udp_manager.default_socket.receive_buffer:
            for j, (data, src_ip) in enumerate(client2.udp_manager.default_socket.receive_buffer):
                try:
                    decoded = data.decode()
                    print(f"Buffer {j}: '{decoded}'")
                    if decoded.startswith("MESSAGE:"):
                        content = decoded[9:]
                        print(f"✅ SUCCESS: [Message from {src_ip}]: {content}")
                        # Clear the buffer for next message
                        client2.udp_manager.default_socket.receive_buffer.clear()
                        break
                except:
                    print(f"Raw buffer {j}: {data}")
        else:
            print("❌ No message received")
    
    # Test manual display
    print(f"\n=== Manual Message Display Test ===")
    print("Sending one more message and checking display...")
    
    test_msg = "FINAL TEST MESSAGE"
    client1.send_message(client2.ip, test_msg, 'udp')
    time.sleep(2)
    
    # Manually process and display
    if client2.udp_manager.default_socket.receive_buffer:
        data, src_ip = client2.udp_manager.default_socket.receive_buffer[-1]
        try:
            decoded = data.decode()
            print(f"Raw received: '{decoded}'")
            if "|" in decoded:
                parts = decoded.split("|", 1)
                if len(parts) > 1:
                    actual_msg = parts[1]
                    if actual_msg.startswith("MESSAGE:"):
                        content = actual_msg[9:]
                        print(f"\n🎉 FINAL SUCCESS:")
                        print(f"[Message from {src_ip}]: {content}")
                    else:
                        print(f"Unexpected format: {actual_msg}")
        except Exception as e:
            print(f"Decode error: {e}")
    
    # Cleanup
    client1.running = False
    client2.running = False
    print(f"\n=== Test Complete ===")

if __name__ == "__main__":
    working_udp_test()
