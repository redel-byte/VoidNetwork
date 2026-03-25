import random
import time

class UDPSocket:
    def __init__(self, node):
        self.node = node
        self.bound_port = None
        self.receive_buffer = []
        self.lock = None
    
    def bind(self, port):
        """Bind to a specific port."""
        self.bound_port = port
        self.node.logger.info(f"[UDP] Bound to port {port}")
    
    def sendto(self, data, dst_ip, dst_port):
        """Send data to destination using UDP."""
        # Create UDP packet with port information
        udp_data = f"{dst_port}|".encode() + data
        packet = self.node.create_packet(dst_ip, 'udp', udp_data)
        
        # Simulate UDP packet loss (higher than TCP)
        if random.random() < 0.1:  # 10% loss for UDP
            self.node.logger.warning(f"[UDP] Packet lost to {dst_ip}:{dst_port}")
            return False
        
        self.node.send_packet(packet, dst_ip)
        self.node.logger.info(f"[UDP] Sent {len(data)} bytes to {dst_ip}:{dst_port}")
        return True
    
    def recvfrom(self, buffer_size):
        """Receive data from buffer."""
        if self.receive_buffer:
            return self.receive_buffer.pop(0)
        return None, None

class UDPManager:
    def __init__(self, node):
        self.node = node
        self.sockets = {}
        self.default_socket = UDPSocket(node)
    
    def handle_packet(self, packet):
        """Handle incoming UDP packet."""
        try:
            # Extract port information and data
            payload_str = packet.payload.decode()
            if '|' not in payload_str:
                # No port info, treat as direct message
                data = packet.payload
                dst_port = self.node.port
            else:
                parts = payload_str.split('|', 1)
                dst_port = int(parts[0])
                data = parts[1].encode() if len(parts) > 1 else b''
            
            self.node.logger.info(f"[UDP] Received {len(data)} bytes from {packet.src_ip} to port {dst_port}")
            
            # Store in receive buffer
            self.default_socket.receive_buffer.append((data, packet.src_ip))
            
            # Process the data based on content type
            self._process_udp_data(data, packet.src_ip, dst_port)
            
        except Exception as e:
            self.node.logger.error(f"[UDP] Error handling packet: {e}")
    
    def _process_udp_data(self, data, src_ip, port):
        """Process received UDP data."""
        try:
            # Try to decode as text message
            message = data.decode()
            if message.startswith("MESSAGE:"):
                # It's a text message
                msg_content = message[9:]  # Remove "MESSAGE:" prefix
                self.node.logger.info(f"[UDP] Message from {src_ip}: {msg_content}")
                print(f"\n[Message from {src_ip}]: {msg_content}")
                
            elif message.startswith("FILE:"):
                # It's file metadata
                parts = message[5:].split('|')
                if len(parts) >= 2:
                    filename = parts[0]
                    file_size = int(parts[1])
                    self.node.logger.info(f"[UDP] Receiving file: {filename} ({file_size} bytes)")
                    
            else:
                # Raw data, could be file content
                self.node.logger.debug(f"[UDP] Raw data from {src_ip}: {len(data)} bytes")
                
        except UnicodeDecodeError:
            # Binary data, likely file content
            self.node.logger.debug(f"[UDP] Binary data from {src_ip}: {len(data)} bytes")
    
    def send_message(self, dst_ip, dst_port, message):
        """Send a text message via UDP."""
        message_data = f"MESSAGE:{message}".encode()
        return self.default_socket.sendto(message_data, dst_ip, dst_port)
    
    def send_file_chunk(self, dst_ip, dst_port, chunk_data, chunk_num, total_chunks):
        """Send a file chunk via UDP."""
        chunk_info = f"CHUNK:{chunk_num}:{total_chunks}|".encode()
        return self.default_socket.sendto(chunk_info + chunk_data, dst_ip, dst_port)