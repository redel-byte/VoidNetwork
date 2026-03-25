import threading
import socket
import time
import random
from utils.logger import get_logger, log_packet_flow
from protocols.arp import ARPTable
from protocols.ip import RoutingTable
from protocols.tcp import TCPManager
from protocols.udp import UDPManager
from core.packet import Packet

class Node:
    def __init__(self, config):
        self.config = config
        self.name = config['name']
        self.ip = config['ip']
        self.port = config['port']  # listening port for direct connections (UDP/TCP)
        self.default_gateway = config.get('default_gateway')
        self.logger = get_logger(self.name)
        self.routing_table = RoutingTable()
        self.arp_table = ARPTable(self)
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # Use UDP for simplicity
        self.socket.bind(('0.0.0.0', self.port))
        self.running = True
        self.receive_thread = threading.Thread(target=self.receive_loop, daemon=True)
        self.receive_thread.start()
        
        # Initialize protocol managers
        self.tcp_manager = TCPManager(self)
        self.udp_manager = UDPManager(self)
        
        # Setup routing table
        self._setup_routing()
        
        # Packet handlers for different protocols
        self.packet_handlers = {
            'tcp': self.handle_tcp,
            'udp': self.handle_udp,
            'arp': self.handle_arp,
        }
        
        self.logger.info(f"Node {self.name} ({self.ip}:{self.port}) initialized")

    def _setup_routing(self):
        """Setup initial routing table."""
        # Add direct routes (connected networks)
        self.routing_table.add_route('127.0.0.1', '255.255.255.255', '127.0.0.1')
        
        # Add default gateway if configured
        if self.default_gateway:
            self.routing_table.add_route('0.0.0.0', '0.0.0.0', self.default_gateway)
            self.logger.info(f"Default gateway set to {self.default_gateway}")
    
    def create_packet(self, dst_ip, protocol, payload, seq=0):
        """Create a new packet."""
        return Packet(self.ip, dst_ip, protocol, payload, seq)
    
    def _broadcast_to_all(self, packet):
        """Broadcast packet to all registered nodes."""
        # This would be implemented in main.py to access the global registry
        pass
    
    def receive_loop(self):
        """Receive packets from the network (UDP)."""
        while self.running:
            try:
                data, addr = self.socket.recvfrom(65535)
                
                # Simulate packet loss (random drop)
                if random.random() < 0.05:  # 5% loss
                    self.logger.info(f"Packet lost (simulated) from {addr}")
                    continue
                
                try:
                    packet = Packet.from_bytes(data)
                    if not packet.is_valid():
                        self.logger.warning(f"Invalid packet checksum from {addr}")
                        continue
                    
                    log_packet_flow(self.logger, "RECV", packet)
                    
                    # Process based on destination
                    if packet.dst_ip == self.ip or packet.dst_ip == "255.255.255.255":
                        # Deliver to higher layer
                        handler = self.packet_handlers.get(packet.protocol)
                        if handler:
                            handler(packet)
                        else:
                            self.logger.warning(f"No handler for protocol {packet.protocol}")
                    else:
                        # Forward packet
                        self.forward_packet(packet)
                        
                except Exception as e:
                    self.logger.error(f"Error parsing packet from {addr}: {e}")
                    
            except socket.timeout:
                continue
            except Exception as e:
                if self.running:  # Only log if not shutting down
                    self.logger.error(f"Error in receive loop: {e}")

    def send_packet(self, packet, dest_ip, dest_port=None):
        """Send packet to next hop (determined by routing)."""
        # Perform ARP resolution first
        mac = self.arp_table.resolve(dest_ip)
        if not mac:
            self.logger.error(f"ARP resolution failed for {dest_ip}")
            return False
        
        # Get next hop from routing table
        next_hop = self.routing_table.get_next_hop(dest_ip)
        if not next_hop:
            self.logger.error(f"No route to {dest_ip}")
            return False
        
        # Resolve next hop to actual address
        host, port = self.resolve_ip_to_address(next_hop)
        if host is None:
            self.logger.error(f"Cannot resolve {next_hop}")
            return False
        
        # Simulate network delay
        time.sleep(random.uniform(0.01, 0.1))
        
        try:
            self.socket.sendto(packet.to_bytes(), (host, port))
            log_packet_flow(self.logger, "SEND", packet, f"via {next_hop}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to send packet: {e}")
            return False

    def resolve_ip_to_address(self, ip):
        """In a real simulation, this would use ARP or a registry. For now, assume localhost with port mapping."""
        # We'll keep a mapping of IP to (host, port) globally.
        # For simplicity, we'll use a global dictionary that nodes register themselves.
        # We'll implement a simple registry in main.
        pass

    def forward_packet(self, packet):
        """Forward packet based on routing table."""
        log_packet_flow(self.logger, "FWD", packet, "forwarding")
        self.send_packet(packet, packet.dst_ip)

    def handle_tcp(self, packet):
        """Handle TCP packets using TCP manager."""
        self.tcp_manager.handle_packet(packet)

    def handle_udp(self, packet):
        """Handle UDP packets using UDP manager."""
        self.udp_manager.handle_packet(packet)
    
    def handle_arp(self, packet):
        """Handle ARP packets."""
        try:
            payload_str = packet.payload.decode()
            if payload_str.startswith("ARP_REQUEST"):
                self.arp_table.handle_arp_request(packet, packet.src_ip)
            elif payload_str.startswith("ARP_REPLY"):
                self.arp_table.handle_arp_reply(packet)
        except Exception as e:
            self.logger.error(f"Error handling ARP packet: {e}")