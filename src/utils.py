# src/utils.py
import json
import socket
import asyncio
import websockets
from pathlib import Path
from datetime import datetime


def get_local_ip():
    """Get the local IP address of the machine"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "127.0.0.1"


async def register_with_server(username, ip, server_url="ws://localhost:8765"):
    """Register user with central server and keep connection alive"""
    try:
        async with websockets.connect(server_url) as websocket:
            # Register with server
            register_message = {
                "type": "register",
                "username": username,
                "ip": ip
            }
            await websocket.send(json.dumps(register_message))
            print(f"✅ Registered with central server: {username} ({ip})")
            
            # KEEP CONNECTION ALIVE - listen for messages
            async for message in websocket:
                data = json.loads(message)
                
                if data["type"] == "ping":
                    # Respond to server pings to keep connection alive
                    await websocket.send(json.dumps({"type": "pong"}))
                elif data["type"] == "user_list":
                    # Optional: handle user list updates
                    pass
                    
            return True
    except Exception as e:
        print(f"❌ Could not connect to central server: {e}")
        return False


async def get_user_ip_from_server(target_username, server_url="ws://localhost:8765"):
    """Get IP address of a user from server"""
    try:
        async with websockets.connect(server_url) as websocket:
            request = {
                "type": "get_ip",
                "target": target_username
            }
            await websocket.send(json.dumps(request))
            
            response = await websocket.recv()
            data = json.loads(response)
            
            if data["type"] == "ip_response" and "ip" in data:
                return data["ip"]
            else:
                return None
    except Exception as e:
        print(f"Error getting IP from server: {e}")
        return None


async def get_online_users(server_url="ws://localhost:8765"):
    """Get list of online users from server"""
    try:
        async with websockets.connect(server_url) as websocket:
            # Listen for user list updates
            async for message in websocket:
                data = json.loads(message)
                if data["type"] == "user_list":
                    return data["users"]
            return []
    except Exception as e:
        print(f"Error getting online users: {e}")
        return []


def get_profile_path():
    """Get the profile directory path"""
    profile_dir = Path.home() / ".chatty_patty"
    profile_dir.mkdir(exist_ok=True)
    return profile_dir


def load_user_profile():
    """Load user profile from file"""
    profile_file = get_profile_path() / "user_profile.json"
    if profile_file.exists():
        with open(profile_file, 'r') as f:
            return json.load(f)
    return None


def save_user_profile(username, ip=None):
    """Save user profile to file"""
    if ip is None:
        ip = get_local_ip()
    
    profile_dir = get_profile_path()
    profile_data = {
        "username": username,
        "ip": ip,
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "last_seen": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "is_online": True
    }
    
    # Save user profile
    with open(profile_dir / "user_profile.json", "w") as f:
        json.dump(profile_data, f, indent=2)
    
    # Add to all users directory
    users_file = profile_dir / "all_users.json"
    users = []
    if users_file.exists():
        with open(users_file, 'r') as f:
            users = json.load(f)
    
    # Check if username already exists
    if not any(u['username'] == username for u in users):
        users.append(profile_data)
        with open(users_file, 'w') as f:
            json.dump(users, f, indent=2)
    
    return profile_data


def load_all_users():
    """Load all users from the local database"""
    users_file = get_profile_path() / "all_users.json"
    if users_file.exists():
        with open(users_file, 'r') as f:
            return json.load(f)
    return []