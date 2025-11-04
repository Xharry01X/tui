import json
from pathlib import Path

def load_config():
    """Load configuration from file"""
    config_file = Path.home() / ".chatty_patty" / "config.json"
    
    # Default configuration
    default_config = {
        "central_server": "ws://192.168.1.16:8765",
        "ping_interval": 20,
        "ping_timeout": 10
    }
    
    if config_file.exists():
        try:
            with open(config_file, 'r') as f:
                user_config = json.load(f)
                # Merge with default config
                default_config.update(user_config)
        except Exception as e:
            print(f"Warning: Could not load config file: {e}")
    
    return default_config

def save_config(config):
    """Save configuration to file"""
    config_file = Path.home() / ".chatty_patty" / "config.json"
    config_file.parent.mkdir(exist_ok=True)
    
    with open(config_file, 'w') as f:
        json.dump(config, f, indent=2)


config = load_config()
CENTRAL_SERVER_URL = config["central_server"]
PING_INTERVAL = config["ping_interval"]
PING_TIMEOUT = config["ping_timeout"]