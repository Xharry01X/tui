# src/utils.py
import asyncio
import json
import logging
import socket
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

SERVER_HOST = "127.0.0.1"
SERVER_PORT = 9999
BUFFER_SIZE = 4096


def get_local_ip() -> str:
    """Get the local IP address of the machine."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        logger.debug("Local IP resolved: %s", ip)
        return ip
    except Exception:
        logger.warning("Could not determine local IP, falling back to 127.0.0.1")
        return "127.0.0.1"


def get_profile_path() -> Path:
    """Get (and create if needed) the profile directory path."""
    profile_dir = Path.home() / ".chatty_patty"
    profile_dir.mkdir(exist_ok=True)
    return profile_dir


def load_user_profile() -> dict | None:
    """Load user profile from disk. Returns dict or None if not found."""
    profile_file = get_profile_path() / "user_profile.json"
    if profile_file.exists():
        with open(profile_file, "r") as f:
            profile = json.load(f)
        logger.debug("User profile loaded for '%s'", profile.get("username"))
        return profile
    logger.debug("No user profile found at %s", profile_file)
    return None


def save_user_profile(username: str, ip: str | None = None) -> dict:
    """Save user profile to disk and append to the all-users directory."""
    if ip is None:
        ip = get_local_ip()
    profile_dir = get_profile_path()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    profile_data = {
        "username": username,
        "ip": ip,
        "created_at": now,
        "last_seen": now,
        "is_online": True,
    }
    # Save individual profile
    profile_file = profile_dir / "user_profile.json"
    with open(profile_file, "w") as f:
        json.dump(profile_data, f, indent=2)
    logger.info("Profile saved for '%s' @ %s", username, ip)

    # Append to all-users directory if not already present
    users_file = profile_dir / "all_users.json"
    users = []
    if users_file.exists():
        with open(users_file, "r") as f:
            users = json.load(f)

    if not any(u["username"] == username for u in users):
        users.append(profile_data)
        with open(users_file, "w") as f:
            json.dump(users, f, indent=2)
        logger.debug("'%s' added to all_users.json", username)
    else:
        logger.debug("'%s' already exists in all_users.json, skipping.", username)

    return profile_data


def load_all_users() -> list:
    """Load all known users from the local database."""
    users_file = get_profile_path() / "all_users.json"
    if users_file.exists():
        with open(users_file, "r") as f:
            users = json.load(f)
        logger.debug("Loaded %d users from all_users.json", len(users))
        return users
    logger.debug("all_users.json not found, returning empty list.")
    return []


async def get_online_users() -> list[str]:
    """
    Query the central server for the list of currently online users.
    Returns a list of usernames that are currently connected.
    """
    try:
        reader, writer = await asyncio.wait_for(
            asyncio.open_connection(SERVER_HOST, SERVER_PORT), timeout=5.0
        )

        # Send query request
        query_msg = json.dumps({"type": "query_users"}) + "\n"
        writer.write(query_msg.encode("utf-8"))
        await writer.drain()

        # Read response
        response_data = await asyncio.wait_for(reader.read(BUFFER_SIZE), timeout=5.0)

        if response_data:
            response = json.loads(response_data.decode("utf-8").strip())
            online_users = response.get("users", [])
            logger.debug("Retrieved %d online users from server", len(online_users))

            writer.close()
            await writer.wait_closed()

            return online_users

        writer.close()
        await writer.wait_closed()
        return []

    except (ConnectionRefusedError, asyncio.TimeoutError) as e:
        logger.warning("Failed to query online users: %s", e)
        return []
    except Exception as e:
        logger.error("Error querying online users: %s", e)
        return []
