from core.node import Node
import threading
import time
import os
from core.packet import Packet

class Client(Node):
    def __init__(self, config):
        super().__init__(config)
        self.send_buffer = []
        self.file_reassembly = {}  # For reassembling received files
        self.files = config.get('files', [])
        
        # Add self to ARP table (simulating known MAC)
        self.arp_table.add(self.ip, f"mac-{self.ip.replace('.', '-')}")
        
        self.logger.info(f"Client {self.name} initialized with files: {self.files}")

    def send_message(self, dst_ip, message, protocol='tcp'):
        """Send a text message using specified protocol."""
        self.logger.info(f"Sending message to {dst_ip} via {protocol.upper()}: {message}")
        
        if protocol.lower() == 'tcp':
            # Use TCP for reliable delivery
            conn = self.tcp_manager.connect(dst_ip, dst_port=5000)
            if conn:
                success = conn.send_data(message.encode())
                if success:
                    self.logger.info(f"[TCP] Message sent successfully")
                else:
                    self.logger.error(f"[TCP] Failed to send message")
        else:
            # Use UDP for faster but unreliable delivery
            success = self.udp_manager.send_message(dst_ip, 5000, message)
            if success:
                self.logger.info(f"[UDP] Message sent successfully")
            else:
                self.logger.error(f"[UDP] Failed to send message")

    def send_file(self, dst_ip, filename, protocol='tcp'):
        """Send a file to another node."""
        # Check if file is in allowed list
        if filename not in self.files:
            self.logger.error(f"File {filename} not in allowed files list")
            return False
        
        # Check if file exists
        if not os.path.exists(filename):
            self.logger.error(f"File {filename} not found")
            return False
        
        try:
            # Read file
            with open(filename, 'rb') as f:
                file_data = f.read()
            
            file_size = len(file_data)
            self.logger.info(f"Sending file {filename} ({file_size} bytes) to {dst_ip} via {protocol.upper()}")
            
            if protocol.lower() == 'tcp':
                # Use TCP for reliable file transfer
                conn = self.tcp_manager.connect(dst_ip, dst_port=5000)
                if conn:
                    # Send file metadata first
                    metadata = f"FILE:{filename}|{file_size}"
                    conn.send_data(metadata.encode())
                    time.sleep(0.1)  # Small delay between metadata and data
                    
                    # Send file data in chunks
                    chunk_size = 1024
                    total_chunks = (file_size + chunk_size - 1) // chunk_size
                    
                    for i in range(0, file_size, chunk_size):
                        chunk = file_data[i:i+chunk_size]
                        chunk_num = i // chunk_size
                        chunk_header = f"CHUNK:{chunk_num}:{total_chunks}:".encode()
                        chunk_data = chunk_header + chunk
                        
                        success = conn.send_data(chunk_data)
                        if not success:
                            self.logger.error(f"Failed to send chunk {chunk_num}")
                            return False
                        
                        self.logger.info(f"Sent chunk {chunk_num + 1}/{total_chunks} ({len(chunk)} bytes)")
                        time.sleep(0.05)  # Small delay between chunks
                    
                    self.logger.info(f"File {filename} sent successfully via TCP")
                    return True
                else:
                    self.logger.error("Failed to establish TCP connection")
                    return False
                    
            else:
                # Use UDP for file transfer (unreliable)
                chunk_size = 512  # Smaller chunks for UDP
                total_chunks = (file_size + chunk_size - 1) // chunk_size
                
                # Send file metadata
                metadata = f"FILE:{filename}|{file_size}"
                self.udp_manager.send_message(dst_ip, 5000, metadata)
                
                # Send file chunks
                for i in range(0, file_size, chunk_size):
                    chunk = file_data[i:i+chunk_size]
                    chunk_num = i // chunk_size
                    success = self.udp_manager.send_file_chunk(dst_ip, 5000, chunk, chunk_num, total_chunks)
                    
                    if not success:
                        self.logger.warning(f"UDP chunk {chunk_num} may have been lost")
                    
                    self.logger.info(f"Sent UDP chunk {chunk_num + 1}/{total_chunks} ({len(chunk)} bytes)")
                    time.sleep(0.02)
                
                self.logger.info(f"File {filename} sent via UDP (some chunks may be lost)")
                return True
                
        except Exception as e:
            self.logger.error(f"Error sending file {filename}: {e}")
            return False
    
    def handle_received_file(self, src_ip, filename, file_data):
        """Handle a completely received file."""
        try:
            # Save received file with prefix
            received_filename = f"received_{filename}"
            with open(received_filename, 'wb') as f:
                f.write(file_data)
            
            self.logger.info(f"[FILE] Received and saved file: {received_filename} ({len(file_data)} bytes)")
            print(f"\n[File received from {src_ip}]: {received_filename}")
            
        except Exception as e:
            self.logger.error(f"Error saving received file: {e}")
    
    def show_files(self):
        """Show available files for sending."""
        print(f"\nAvailable files for {self.name}:")
        for filename in self.files:
            if os.path.exists(filename):
                size = os.path.getsize(filename)
                print(f"  - {filename} ({size} bytes)")
            else:
                print(f"  - {filename} (file not found)")
    
    def show_status(self):
        """Show client status information."""
        print(f"\n=== {self.name} Status ===")
        print(f"IP: {self.ip}")
        print(f"Port: {self.port}")
        print(f"Default Gateway: {self.default_gateway or 'None'}")
        print(f"Available Files: {len(self.files)}")
        
        # Show ARP table
        arp_info = self.arp_table.show_table()
        print(arp_info)
        
        # Show routing table
        print(f"\nRouting Table:")
        for route in self.routing_table.routes:
            print(f"  {route[0]}/{route[1]} via {route[2]}")

    def send_data(self, dst_ip, data):
        """Send data using TCP with fragmentation and retransmission."""
        # Break data into packets (fragmentation)
        seq = 0
        offset = 0
        more_frags = True
        while more_frags:
            chunk = data[offset:offset+Packet.MAX_PAYLOAD]
            if offset + Packet.MAX_PAYLOAD >= len(data):
                more_frags = False
            packet = Packet(self.ip, dst_ip, 'tcp', chunk, seq, offset//Packet.MAX_PAYLOAD, more_frags)
            self.send_packet(packet, dst_ip)
            offset += len(chunk)
            seq += 1
            # Simulate retransmission if no ACK received (simplified)