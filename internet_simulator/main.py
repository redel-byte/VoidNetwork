import sys
import os
import argparse
import threading
from utils.config_loader import load_config
from core.client import Client
from core.router import Router
from cli import NodeCLI

# Global registry: IP -> (host, port)
REGISTRY = {}
REGISTRY_LOCK = threading.Lock()

def register_node(ip, host, port):
    """Register a node in the global registry."""
    with REGISTRY_LOCK:
        REGISTRY[ip] = (host, port)
        print(f"Registered node {ip} at {host}:{port}")

def resolve_ip(ip):
    """Resolve IP to (host, port) from registry."""
    with REGISTRY_LOCK:
        return REGISTRY.get(ip)

def get_all_registered_nodes():
    """Get all registered nodes."""
    with REGISTRY_LOCK:
        return dict(REGISTRY)

# Enhanced Node method for broadcasting
def _broadcast_to_all(self, packet):
    """Broadcast packet to all registered nodes."""
    nodes = get_all_registered_nodes()
    for ip, (host, port) in nodes.items():
        if ip != self.ip:  # Don't send to self
            try:
                self.socket.sendto(packet.to_bytes(), (host, port))
                self.logger.debug(f"Broadcast sent to {ip}:{port}")
            except Exception as e:
                self.logger.error(f"Failed to broadcast to {ip}: {e}")

def resolve_ip_to_address(self, ip):
    """Resolve IP to (host, port) using global registry."""
    result = resolve_ip(ip)
    if result:
        self.logger.debug(f"Resolved {ip} to {result}")
    else:
        self.logger.warning(f"Could not resolve {ip}")
    return result

# Patch Node class with enhanced methods
from core.node import Node
Node._broadcast_to_all = _broadcast_to_all
Node.resolve_ip_to_address = resolve_ip_to_address

def main():
    parser = argparse.ArgumentParser(description="Internet Simulator Node")
    parser.add_argument('--config', required=True, help="Path to JSON config file")
    parser.add_argument('--verbose', '-v', action='store_true', help="Enable verbose logging")
    args = parser.parse_args()

    try:
        config = load_config(args.config)
        role = config['role']
        
        # Create node based on role
        if role == 'client':
            node = Client(config)
        elif role == 'router':
            node = Router(config)
        else:
            print(f"Unknown role: {role}")
            sys.exit(1)

        # Register this node with the registry (assume host is localhost for simplicity)
        host = '127.0.0.1'
        register_node(config['ip'], host, config['port'])

        print(f"\n{'='*50}")
        print(f"Internet Simulator - {node.name} ({role.upper()})")
        print(f"IP: {node.ip}")
        print(f"Port: {node.port}")
        print(f"Config: {args.config}")
        print(f"{'='*50}\n")

        # Start CLI in a separate thread
        cli = NodeCLI(node)
        cli_thread = threading.Thread(target=cli.cmdloop, daemon=True)
        cli_thread.start()

        # Wait for the node to finish
        try:
            while node.running:
                threading.Event().wait(1)
        except KeyboardInterrupt:
            print("\nReceived interrupt signal...")
        finally:
            node.running = False
            print(f"Shutting down {node.name}...")
            
            # Clean up registry
            with REGISTRY_LOCK:
                if config['ip'] in REGISTRY:
                    del REGISTRY[config['ip']]
            
            print("Shutdown complete.")

    except FileNotFoundError as e:
        print(f"Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()