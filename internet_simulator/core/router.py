from core.node import Node
import time

class Router(Node):
    def __init__(self, config):
        super().__init__(config)
        self.forwarded_packets = 0
        self.dropped_packets = 0
        
        # Add self to ARP table
        self.arp_table.add(self.ip, f"mac-{self.ip.replace('.', '-')}")
        
        # Setup routing table for router
        self._setup_router_routes()
        
        self.logger.info(f"Router {self.name} initialized and ready to forward packets")

    def _setup_router_routes(self):
        """Setup routing table for router."""
        # Add direct connections to all possible clients
        # In a real scenario, this would be configured dynamically
        client_networks = [
            ('192.168.1.2', '255.255.255.255', '192.168.1.2'),  # Ali
            ('192.168.1.3', '255.255.255.255', '192.168.1.3'),  # Bella
        ]
        
        for dest, mask, gateway in client_networks:
            self.routing_table.add_route(dest, mask, gateway)
        
        self.logger.info("Router routing table configured")

    def forward_packet(self, packet):
        """Forward packet with routing logic."""
        self.forwarded_packets += 1
        
        # Log the forwarding action
        self.logger.info(f"[ROUTER] Forwarding packet: {packet.src_ip} -> {packet.dst_ip}")
        
        # Check if we have a route to destination
        next_hop = self.routing_table.get_next_hop(packet.dst_ip)
        if not next_hop:
            self.logger.warning(f"[ROUTER] No route to {packet.dst_ip}, dropping packet")
            self.dropped_packets += 1
            return False
        
        # Simulate routing delay
        time.sleep(0.01)
        
        # Forward the packet
        success = self.send_packet(packet, packet.dst_ip)
        
        if success:
            self.logger.info(f"[ROUTER] Successfully forwarded to {packet.dst_ip}")
        else:
            self.logger.error(f"[ROUTER] Failed to forward to {packet.dst_ip}")
            self.dropped_packets += 1
        
        return success

    def handle_tcp(self, packet):
        """Handle TCP packets (forwarding only for router)."""
        if packet.dst_ip != self.ip:
            # Forward to destination
            self.forward_packet(packet)
        else:
            # Packet destined for router (shouldn't happen in normal operation)
            self.logger.warning(f"[ROUTER] Received TCP packet destined for router: {packet.payload[:50]}")

    def handle_udp(self, packet):
        """Handle UDP packets (forwarding only for router)."""
        if packet.dst_ip != self.ip:
            # Forward to destination
            self.forward_packet(packet)
        else:
            # Packet destined for router
            self.logger.warning(f"[ROUTER] Received UDP packet destined for router: {packet.payload[:50]}")

    def handle_arp(self, packet):
        """Handle ARP packets (router participates in ARP)."""
        try:
            payload_str = packet.payload.decode()
            if payload_str.startswith("ARP_REQUEST"):
                self.arp_table.handle_arp_request(packet, packet.src_ip)
            elif payload_str.startswith("ARP_REPLY"):
                self.arp_table.handle_arp_reply(packet)
        except Exception as e:
            self.logger.error(f"[ROUTER] Error handling ARP packet: {e}")

    def show_routing_stats(self):
        """Display routing statistics."""
        print(f"\n=== Router {self.name} Statistics ===")
        print(f"Packets Forwarded: {self.forwarded_packets}")
        print(f"Packets Dropped: {self.dropped_packets}")
        if self.forwarded_packets > 0:
            drop_rate = (self.dropped_packets / (self.forwarded_packets + self.dropped_packets)) * 100
            print(f"Drop Rate: {drop_rate:.2f}%")
        
        # Show routing table
        print(f"\nRouting Table:")
        for route in self.routing_table.routes:
            print(f"  {route[0]}/{route[1]} via {route[2]}")
        
        # Show ARP table
        arp_info = self.arp_table.show_table()
        print(arp_info)
