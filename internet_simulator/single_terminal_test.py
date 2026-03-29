#!/usr/bin/env python3
"""
Single Terminal Test - Run multiple nodes in one terminal for testing
This bypasses the global registry issue by keeping all nodes in one process.
"""

import threading
import time
import sys
import signal
from utils.config_loader import load_config
from core.client import Client
from core.router import Router
from main import register_node, get_all_registered_nodes

# Global flag for shutdown
shutdown_flag = False

def signal_handler(sig, frame):
    global shutdown_flag
    print('\nShutting down all nodes...')
    shutdown_flag = True
    sys.exit(0)

def run_cli(node):
    """Run CLI for a node in a separate thread"""
    from cli import NodeCLI
    cli = NodeCLI(node)
    try:
        while not shutdown_flag:
            try:
                cli.cmdloop()
                break
            except KeyboardInterrupt:
                break
    except Exception as e:
        print(f"CLI error for {node.name}: {e}")

def main():
    signal.signal(signal.SIGINT, signal_handler)
    
    print("=== Internet Simulator - Single Terminal Test ===")
    print("Starting all nodes in one process...")
    print()
    
    # Start Router
    print("1. Starting Router...")
    try:
        router_config = load_config('configs/router.json')
        router = Router(router_config)
        register_node(router_config['ip'], '127.0.0.1', router_config['port'])
        print(f"   Router started: {router.name} ({router.ip}:{router.port})")
    except Exception as e:
        print(f"   Router error: {e}")
        return
    
    time.sleep(1)
    
    # Start User Client
    print("2. Starting User Client...")
    try:
        user_config = load_config('configs/user.json')
        user_client = Client(user_config)
        register_node(user_config['ip'], '127.0.0.1', user_config['port'])
        print(f"   User started: {user_client.name} ({user_client.ip}:{user_client.port})")
    except Exception as e:
        print(f"   User error: {e}")
        return
    
    time.sleep(1)
    
    # Start Ali Client
    print("3. Starting Ali Client...")
    try:
        ali_config = load_config('configs/ali.json')
        ali_client = Client(ali_config)
        register_node(ali_config['ip'], '127.0.0.1', ali_config['port'])
        print(f"   Ali started: {ali_client.name} ({ali_client.ip}:{ali_client.port})")
    except Exception as e:
        print(f"   Ali error: {e}")
        return
    
    time.sleep(1)
    
    print()
    print("=== All Nodes Started Successfully ===")
    print("Registered nodes:")
    for ip, (host, port) in get_all_registered_nodes().items():
        print(f"  {ip} -> {host}:{port}")
    print()
    print("=== Testing Communication ===")
    
    # Test UDP message from User to Ali
    print("1. Testing UDP message from User to Ali...")
    try:
        user_client.send_message(ali_client.ip, "Hello Ali from User!", "udp")
        time.sleep(2)
        print("   UDP message sent")
    except Exception as e:
        print(f"   UDP error: {e}")
    
    # Test UDP message from Ali to User
    print("2. Testing UDP message from Ali to User...")
    try:
        ali_client.send_message(user_client.ip, "Hello User from Ali!", "udp")
        time.sleep(2)
        print("   UDP message sent")
    except Exception as e:
        print(f"   UDP error: {e}")
    
    print()
    print("=== Interactive Mode ===")
    print("You can now test manually:")
    print("  user_client.send_message('192.168.1.2', 'your message', 'udp')")
    print("  ali_client.send_message('192.168.1.6', 'your message', 'udp')")
    print()
    print("Press Ctrl+C to shutdown all nodes")
    
    # Keep running until shutdown
    try:
        while not shutdown_flag:
            time.sleep(1)
    except KeyboardInterrupt:
        pass
    
    # Cleanup
    print("Shutting down...")
    router.running = False
    user_client.running = False
    ali_client.running = False
    print("All nodes shut down.")

if __name__ == "__main__":
    main()
