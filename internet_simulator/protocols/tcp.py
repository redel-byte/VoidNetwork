import threading
import time
import random
from enum import Enum

class TCPState(Enum):
    CLOSED = "CLOSED"
    SYN_SENT = "SYN_SENT"
    SYN_RECEIVED = "SYN_RECEIVED"
    ESTABLISHED = "ESTABLISHED"
    FIN_WAIT_1 = "FIN_WAIT_1"
    FIN_WAIT_2 = "FIN_WAIT_2"
    CLOSE_WAIT = "CLOSE_WAIT"
    CLOSING = "CLOSING"
    LAST_ACK = "LAST_ACK"
    TIME_WAIT = "TIME_WAIT"

class TCPConnection:
    def __init__(self, src_ip, src_port, dst_ip, dst_port, node):
        self.src_ip = src_ip
        self.src_port = src_port
        self.dst_ip = dst_ip
        self.dst_port = dst_port
        self.node = node
        self.state = TCPState.CLOSED
        self.seq_num = random.randint(0, 2**32 - 1)
        self.ack_num = 0
        self.window_size = 1024
        self.send_buffer = []
        self.receive_buffer = {}
        self.unacked_packets = {}
        self.lock = threading.Lock()
        self.connection_established = threading.Event()
        
    def send_syn(self):
        """Send SYN packet to initiate connection."""
        with self.lock:
            self.state = TCPState.SYN_SENT
            self.node.logger.info(f"[TCP] SYN sent to {self.dst_ip}:{self.dst_port} (seq={self.seq_num})")
            
            # Create SYN packet (no payload, just SYN flag)
            syn_data = f"SYN|{self.seq_num}|0".encode()
            packet = self.node.create_packet(self.dst_ip, 'tcp', syn_data, self.seq_num)
            self.node.send_packet(packet, self.dst_ip)
            
            # Start retransmission timer
            self._start_retransmission_timer(packet, "SYN")
    
    def handle_syn(self, packet):
        """Handle incoming SYN packet."""
        with self.lock:
            seq = int(packet.payload.decode().split('|')[1])
            self.ack_num = seq + 1
            self.state = TCPState.SYN_RECEIVED
            self.node.logger.info(f"[TCP] SYN received from {packet.src_ip} (seq={seq})")
            
            # Send SYN-ACK
            syn_ack_data = f"SYN-ACK|{self.seq_num}|{self.ack_num}".encode()
            response = self.node.create_packet(packet.src_ip, 'tcp', syn_ack_data, self.seq_num)
            self.node.send_packet(response, packet.src_ip)
            self.node.logger.info(f"[TCP] SYN-ACK sent (seq={self.seq_num}, ack={self.ack_num})")
    
    def handle_syn_ack(self, packet):
        """Handle SYN-ACK packet."""
        with self.lock:
            parts = packet.payload.decode().split('|')
            seq = int(parts[1])
            ack = int(parts[2])
            
            if self.state == TCPState.SYN_SENT:
                self.ack_num = seq + 1
                self.seq_num = ack
                self.state = TCPState.ESTABLISHED
                self.connection_established.set()
                self.node.logger.info(f"[TCP] SYN-ACK received (seq={seq}, ack={ack})")
                
                # Send ACK
                ack_data = f"ACK|{self.seq_num}|{self.ack_num}".encode()
                response = self.node.create_packet(packet.src_ip, 'tcp', ack_data, self.seq_num)
                self.node.send_packet(response, packet.src_ip)
                self.node.logger.info(f"[TCP] ACK sent (seq={self.seq_num}, ack={self.ack_num})")
                self.node.logger.info(f"[TCP] Connection established with {packet.src_ip}")
    
    def handle_ack(self, packet):
        """Handle ACK packet."""
        with self.lock:
            parts = packet.payload.decode().split('|')
            ack = int(parts[2])
            
            # Remove acknowledged packets from unacked list
            if ack in self.unacked_packets:
                del self.unacked_packets[ack]
                self.node.logger.debug(f"[TCP] ACK received for seq={ack}")
    
    def send_data(self, data):
        """Send data with sequence numbers and retransmission."""
        # Wait for connection to be established
        if not self.connection_established.wait(timeout=10):
            self.node.logger.error("[TCP] Connection timeout")
            return False
        
        with self.lock:
            # Split data into chunks
            chunk_size = 512
            chunks = [data[i:i+chunk_size] for i in range(0, len(data), chunk_size)]
            
            for i, chunk in enumerate(chunks):
                seq = self.seq_num + i
                packet_data = f"DATA|{seq}|{len(chunk)}|".encode() + chunk
                packet = self.node.create_packet(self.dst_ip, 'tcp', packet_data, seq)
                
                # Store for retransmission
                self.unacked_packets[seq] = {
                    'packet': packet,
                    'timestamp': time.time(),
                    'retries': 0
                }
                
                self.node.send_packet(packet, self.dst_ip)
                self.node.logger.info(f"[TCP] Sent data chunk {i+1}/{len(chunks)} (seq={seq}, size={len(chunk)})")
            
            return True
    
    def handle_data(self, packet):
        """Handle incoming data packet."""
        with self.lock:
            parts = packet.payload.decode().split('|', 3)
            if len(parts) < 4:
                return
                
            seq = int(parts[1])
            size = int(parts[2])
            data = parts[3].encode()
            
            self.receive_buffer[seq] = data
            self.ack_num = seq + size
            
            self.node.logger.info(f"[TCP] Received data chunk (seq={seq}, size={size})")
            
            # Send ACK
            ack_data = f"ACK|{self.seq_num}|{self.ack_num}".encode()
            response = self.node.create_packet(packet.src_ip, 'tcp', ack_data, self.seq_num)
            self.node.send_packet(response, packet.src_ip)
    
    def _start_retransmission_timer(self, packet, packet_type):
        """Start retransmission timer for reliable delivery."""
        def retransmit():
            time.sleep(1.0)  # Initial timeout
            if self.state in [TCPState.SYN_SENT, TCPState.ESTABLISHED]:
                self.node.logger.warning(f"[TCP] Retransmitting {packet_type}")
                self.node.send_packet(packet, self.dst_ip)
                # Exponential backoff
                self._start_retransmission_timer(packet, packet_type)
        
        thread = threading.Thread(target=retransmit, daemon=True)
        thread.start()

class TCPManager:
    def __init__(self, node):
        self.node = node
        self.connections = {}
        self.listen_sockets = {}
        self.lock = threading.Lock()
    
    def connect(self, dst_ip, dst_port):
        """Initiate TCP connection to destination."""
        conn_key = f"{dst_ip}:{dst_port}"
        with self.lock:
            if conn_key in self.connections:
                return self.connections[conn_key]
            
            conn = TCPConnection(self.node.ip, self.node.port, dst_ip, dst_port, self.node)
            self.connections[conn_key] = conn
            conn.send_syn()
            return conn
    
    def handle_packet(self, packet):
        """Handle incoming TCP packet."""
        try:
            payload_str = packet.payload.decode()
            if '|' not in payload_str:
                return
                
            packet_type = payload_str.split('|')[0]
            conn_key = f"{packet.src_ip}:{packet.src_port}"
            
            with self.lock:
                if packet_type == "SYN":
                    # Create new connection for incoming SYN
                    conn = TCPConnection(self.node.ip, self.node.port, packet.src_ip, packet.src_port, self.node)
                    self.connections[conn_key] = conn
                    conn.handle_syn(packet)
                    
                elif conn_key in self.connections:
                    conn = self.connections[conn_key]
                    
                    if packet_type == "SYN-ACK":
                        conn.handle_syn_ack(packet)
                    elif packet_type == "ACK":
                        conn.handle_ack(packet)
                    elif packet_type == "DATA":
                        conn.handle_data(packet)
                        
        except Exception as e:
            self.node.logger.error(f"[TCP] Error handling packet: {e}")
    
    def get_connection_data(self, src_ip):
        """Get reassembled data from connection."""
        with self.lock:
            for conn_key, conn in self.connections.items():
                if src_ip in conn_key:
                    # Sort by sequence number and reassemble
                    sorted_data = sorted(conn.receive_buffer.items())
                    return b''.join([data for seq, data in sorted_data])
        return None