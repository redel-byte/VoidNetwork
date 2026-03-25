import json
import os

def load_config(config_path):
    """Load and validate a node's configuration."""
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Config file {config_path} not found.")
    with open(config_path, 'r') as f:
        config = json.load(f)
    required_fields = ['name', 'ip', 'role', 'port']
    for field in required_fields:
        if field not in config:
            raise ValueError(f"Missing required field: {field}")
    # Default for files if not present
    config.setdefault('files', [])
    config.setdefault('default_gateway', None)
    return config