#!/usr/bin/env python3
"""
Shared registry for multi-terminal communication
Uses a JSON file to share node information between processes
"""

import json
import os
import time
import threading
from pathlib import Path

REGISTRY_FILE = "node_registry.json"

class SharedRegistry:
    def __init__(self):
        self.lock = threading.Lock()
        self._ensure_registry_file()
    
    def _ensure_registry_file(self):
        """Create registry file if it doesn't exist"""
        if not os.path.exists(REGISTRY_FILE):
            with open(REGISTRY_FILE, 'w') as f:
                json.dump({}, f)
    
    def register_node(self, ip, host, port):
        """Register a node"""
        with self.lock:
            try:
                # Read existing registry
                with open(REGISTRY_FILE, 'r') as f:
                    registry = json.load(f)
                
                # Add/update node
                registry[ip] = {
                    'host': host,
                    'port': port,
                    'timestamp': time.time()
                }
                
                # Write back
                with open(REGISTRY_FILE, 'w') as f:
                    json.dump(registry, f, indent=2)
                
                print(f"Registered node {ip} at {host}:{port}")
                return True
            except Exception as e:
                print(f"Error registering node: {e}")
                return False
    
    def get_node_address(self, ip):
        """Get node address by IP"""
        with self.lock:
            try:
                with open(REGISTRY_FILE, 'r') as f:
                    registry = json.load(f)
                
                if ip in registry:
                    node = registry[ip]
                    return (node['host'], node['port'])
                return None
            except Exception as e:
                print(f"Error getting node address: {e}")
                return None
    
    def get_all_nodes(self):
        """Get all registered nodes"""
        with self.lock:
            try:
                with open(REGISTRY_FILE, 'r') as f:
                    registry = json.load(f)
                
                return {ip: (node['host'], node['port']) 
                       for ip, node in registry.items()}
            except Exception as e:
                print(f"Error getting all nodes: {e}")
                return {}
    
    def unregister_node(self, ip):
        """Remove a node from registry"""
        with self.lock:
            try:
                with open(REGISTRY_FILE, 'r') as f:
                    registry = json.load(f)
                
                if ip in registry:
                    del registry[ip]
                
                with open(REGISTRY_FILE, 'w') as f:
                    json.dump(registry, f, indent=2)
                
                print(f"Unregistered node {ip}")
                return True
            except Exception as e:
                print(f"Error unregistering node: {e}")
                return False

# Global shared registry instance
shared_registry = SharedRegistry()

def register_shared_node(ip, host, port):
    """Register node in shared registry"""
    return shared_registry.register_node(ip, host, port)

def get_shared_node_address(ip):
    """Get node address from shared registry"""
    return shared_registry.get_node_address(ip)

def get_all_shared_nodes():
    """Get all nodes from shared registry"""
    return shared_registry.get_all_nodes()

def unregister_shared_node(ip):
    """Unregister node from shared registry"""
    return shared_registry.unregister_node(ip)

def cleanup_registry():
    """Clean up old entries (older than 5 minutes)"""
    with shared_registry.lock:
        try:
            with open(REGISTRY_FILE, 'r') as f:
                registry = json.load(f)
            
            current_time = time.time()
            cutoff_time = current_time - 300  # 5 minutes
            
            cleaned_registry = {
                ip: node for ip, node in registry.items()
                if node['timestamp'] > cutoff_time
            }
            
            with open(REGISTRY_FILE, 'w') as f:
                json.dump(cleaned_registry, f, indent=2)
                
        except Exception as e:
            print(f"Error cleaning registry: {e}")
