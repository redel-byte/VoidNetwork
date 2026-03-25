class RoutingTable:
    def __init__(self):
        self.routes = []  # list of (destination, netmask, gateway)

    def add_route(self, dest, netmask, gateway):
        self.routes.append((dest, netmask, gateway))

    def get_next_hop(self, dest_ip):
        """Find the best match route."""
        # Simple longest prefix match.
        # For now, just return gateway if dest matches a route.
        # If no route, return None.
        for dest, netmask, gateway in self.routes:
            # Simplified: if dest is '0.0.0.0' (default), match all.
            if dest == '0.0.0.0':
                return gateway
            # In real simulation, we'd check network prefix.
            # For simplicity, exact match or default.
            if dest == dest_ip:
                return gateway
        return None