import time
import threading
import random

class ARPTable:
    def __init__(self, node):
        self.table = {}  # ip -> mac
        self.node = node
        self.pending_requests = {}  # ip -> timestamp
        self.lock = threading.Lock()
    
    def add(self, ip, mac):
        """Add or update ARP entry."""
        with self.lock:
            self.table[ip] = mac
            self.node.logger.info(f"[ARP] Added entry: {ip} -> {mac}")
    
    def get(self, ip):
        """Get MAC address for IP."""
        with self.lock:
            return self.table.get(ip)
    
    def resolve(self, target_ip):
        """Resolve IP to MAC using ARP request/reply."""
        # Check if already in table
        mac = self.get(target_ip)
        if mac:
            return mac
        
        # Send ARP request
        self._send_arp_request(target_ip)
        
        # Wait for reply (simplified - in real implementation would use proper waiting)
        time.sleep(0.5)
        
        # Check again
        return self.get(target_ip)
    
    def _send_arp_request(self, target_ip):
        """Send ARP request for target IP."""
        with self.lock:
            if target_ip in self.pending_requests:
                # Already requested, don't spam
                return
            
            self.pending_requests[target_ip] = time.time()
            self.node.logger.info(f"[ARP] Sending request: Who has {target_ip}?")
        
        # Create ARP request packet
        arp_data = f"ARP_REQUEST|{target_ip}".encode()
        packet = self.node.create_packet("255.255.255.255", 'arp', arp_data)  # Broadcast
        
        # Send to all known nodes (simplified broadcast)
        self._broadcast_packet(packet)
        
        # Start timeout to remove pending request
        threading.Timer(2.0, self._remove_pending_request, args=[target_ip]).start()
    
    def handle_arp_request(self, packet, src_ip):
        """Handle incoming ARP request."""
        try:
            payload_str = packet.payload.decode()
            if not payload_str.startswith("ARP_REQUEST|"):
                return
            
            target_ip = payload_str.split('|')[1]
            
            # If the target is our IP, send ARP reply
            if target_ip == self.node.ip:
                self._send_arp_reply(src_ip)
                self.node.logger.info(f"[ARP] Received request for {target_ip}, sending reply")
            
        except Exception as e:
            self.node.logger.error(f"[ARP] Error handling request: {e}")
    
    def handle_arp_reply(self, packet):
        """Handle incoming ARP reply."""
        try:
            payload_str = packet.payload.decode()
            if not payload_str.startswith("ARP_REPLY|"):
                return
            
            parts = payload_str.split('|')
            src_ip = parts[1]
            mac = parts[2]
            
            # Add to ARP table
            self.add(src_ip, mac)
            self.node.logger.info(f"[ARP] Received reply: {src_ip} -> {mac}")
            
            # Remove from pending requests
            with self.lock:
                if src_ip in self.pending_requests:
                    del self.pending_requests[src_ip]
            
        except Exception as e:
            self.node.logger.error(f"[ARP] Error handling reply: {e}")
    
    def _send_arp_reply(self, target_ip):
        """Send ARP reply to target IP."""
        # Generate a fake MAC address for simulation
        mac = f"mac-{self.node.ip.replace('.', '-')}"
        
        arp_data = f"ARP_REPLY|{self.node.ip}|{mac}".encode()
        packet = self.node.create_packet(target_ip, 'arp', arp_data)
        
        # Send directly to target using the global registry
        from main import resolve_ip
        target_address = resolve_ip(target_ip)
        if target_address:
            host, port = target_address
            self.node.socket.sendto(packet.to_bytes(), (host, port))
            self.node.logger.info(f"[ARP] Sent reply directly to {target_ip} at {host}:{port}")
        else:
            # Fallback: try to send packet normally
            self.node.send_packet(packet, target_ip)
    
    def _broadcast_packet(self, packet):
        """Broadcast packet to all known nodes."""
        # Send to all registered nodes using global registry
        from main import get_all_registered_nodes
        nodes = get_all_registered_nodes()
        
        for ip, (host, port) in nodes.items():
            if ip != self.node.ip:  # Don't send to self
                try:
                    self.node.socket.sendto(packet.to_bytes(), (host, port))
                    self.node.logger.debug(f"[ARP] Broadcast sent to {ip}:{port}")
                except Exception as e:
                    self.node.logger.error(f"[ARP] Failed to broadcast to {ip}: {e}")
    
    def _remove_pending_request(self, target_ip):
        """Remove pending request after timeout."""
        with self.lock:
            if target_ip in self.pending_requests:
                del self.pending_requests[target_ip]
                self.node.logger.warning(f"[ARP] Request timeout for {target_ip}")
    
    def show_table(self):
        """Display ARP table."""
        with self.lock:
            if not self.table:
                return "ARP table is empty"
            
            result = "ARP Table:\n"
            result += "IP Address\t\tMAC Address\n"
            result += "-" * 40 + "\n"
            for ip, mac in self.table.items():
                result += f"{ip}\t\t{mac}\n"
            return result

class ARPPacket:
    """ARP packet structure for simulation."""
    def __init__(self, opcode, sender_ip, sender_mac, target_ip, target_mac="00:00:00:00:00:00"):
        self.opcode = opcode  # REQUEST or REPLY
        self.sender_ip = sender_ip
        self.sender_mac = sender_mac
        self.target_ip = target_ip
        self.target_mac = target_mac
    
    def to_bytes(self):
        """Serialize ARP packet."""
        data = f"{self.opcode}|{self.sender_ip}|{self.sender_mac}|{self.target_ip}|{self.target_mac}"
        return data.encode()
    
    @classmethod
    def from_bytes(cls, data):
        """Deserialize ARP packet."""
        parts = data.decode().split('|')
        if len(parts) != 5:
            return None
        
        return cls(parts[0], parts[1], parts[2], parts[3], parts[4])