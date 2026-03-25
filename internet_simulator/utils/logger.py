import logging
import sys
import os
from datetime import datetime

class ColoredFormatter(logging.Formatter):
    """Custom formatter with colors for different log levels and protocols."""
    
    # ANSI color codes
    COLORS = {
        'DEBUG': '\033[36m',      # Cyan
        'INFO': '\033[32m',       # Green
        'WARNING': '\033[33m',    # Yellow
        'ERROR': '\033[31m',      # Red
        'CRITICAL': '\033[35m',   # Magenta
        'RESET': '\033[0m',       # Reset
    }
    
    # Protocol-specific colors
    PROTOCOL_COLORS = {
        '[TCP]': '\033[94m',      # Bright Blue
        '[UDP]': '\033[93m',      # Bright Yellow
        '[ARP]': '\033[95m',      # Bright Magenta
        '[DNS]': '\033[96m',      # Bright Cyan
        '[ROUTER]': '\033[92m',   # Bright Green
        '[CLIENT]': '\033[97m',   # Bright White
    }
    
    def format(self, record):
        # Get the original formatted message
        message = super().format(record)
        
        # Apply color based on log level
        level_color = self.COLORS.get(record.levelname, '')
        reset = self.COLORS['RESET']
        
        # Apply protocol-specific colors if present
        for protocol, color in self.PROTOCOL_COLORS.items():
            if protocol in message:
                message = message.replace(protocol, f"{color}{protocol}{reset}")
                break
        
        # Apply level color to the entire message
        if level_color:
            message = f"{level_color}{message}{reset}"
        
        return message

def get_logger(name):
    """Get a configured logger with colored output and file logging."""
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    
    # Clear existing handlers to avoid duplicates
    logger.handlers.clear()
    
    # Create logs directory if not exists
    if not os.path.exists('logs'):
        os.makedirs('logs')
    
    # File handler (no colors for file)
    file_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler = logging.FileHandler(f'logs/{name}.log', mode='a', encoding='utf-8')
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(file_formatter)
    
    # Console handler with colors
    console_formatter = ColoredFormatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(console_formatter)
    
    # Add handlers
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger

def setup_network_logging():
    """Setup logging configuration for the entire network simulator."""
    # Create a root logger configuration
    logging.getLogger().setLevel(logging.WARNING)  # Reduce noise from other libraries
    
    # Custom log levels for network events
    logging.addLevelName(15, "NETWORK")  # Between DEBUG(10) and INFO(20)
    
    return True

# Network-specific logging functions
def log_network_event(logger, event_type, message, level=logging.INFO):
    """Log network-specific events with consistent formatting."""
    formatted_message = f"[{event_type}] {message}"
    logger.log(level, formatted_message)

def log_packet_flow(logger, direction, packet, additional_info=""):
    """Log packet flow with detailed information."""
    if direction == "SEND":
        flow_msg = f"→ {packet.src_ip} → {packet.dst_ip} ({packet.protocol})"
    elif direction == "RECV":
        flow_msg = f"← {packet.src_ip} ← {packet.dst_ip} ({packet.protocol})"
    elif direction == "FWD":
        flow_msg = f"↔ {packet.src_ip} ↔ {packet.dst_ip} ({packet.protocol}) [FORWARD]"
    else:
        flow_msg = f"? {packet.src_ip} ? {packet.dst_ip} ({packet.protocol})"
    
    if additional_info:
        flow_msg += f" - {additional_info}"
    
    logger.info(f"[PACKET] {flow_msg}")

def log_protocol_state(logger, protocol, state, details=""):
    """Log protocol state changes."""
    state_msg = f"[{protocol}] State: {state}"
    if details:
        state_msg += f" - {details}"
    logger.info(state_msg)