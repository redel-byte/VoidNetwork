class RoutingTable:
    def __init__(self):
        self.routes = []  # list of (destination, netmask, gateway)

    def add_route(self, dest, netmask, gateway):
        self.routes.append((dest, netmask, gateway))

    def get_next_hop(self, dest_ip):
        """Find the best match route."""
        # First check for exact match (direct connection)
        for dest, netmask, gateway in self.routes:
            if dest == dest_ip:
                return dest_ip  # Direct connection
        
        # Check if this is the same network (simplified - assume /24)
        dest_network = '.'.join(dest_ip.split('.')[:-1]) + '.0'
        for dest, netmask, gateway in self.routes:
            if dest.endswith('.0') and dest_ip.startswith(dest[:-1]):
                return dest_ip  # Same network, direct connection
        
        # Then check for default route
        for dest, netmask, gateway in self.routes:
            if dest == '0.0.0.0':  # Default route
                return gateway
        
        # If no route found, try direct connection as fallback
        return dest_ip