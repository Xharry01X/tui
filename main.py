from src.profile_setup import ProfileSetup
from src.users_discovery import UserDirectory
from src.utils import load_user_profile, get_local_ip
import asyncio
import threading


def start_websocket_connection(username, ip):
    """Start WebSocket connection in background thread"""
    async def keep_alive():
        from src.utils import register_with_server
        print(f"🌐 Starting WebSocket connection for {username}...")
        await register_with_server(username, ip)
    
    def run_loop():
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(keep_alive())
        except Exception as e:
            print(f"💥 WebSocket connection failed: {e}")
    
    thread = threading.Thread(target=run_loop, daemon=True)
    thread.start()
    print(f"🔗 Background WebSocket thread started for {username}")


def main():
    user_profile = load_user_profile()
    
    if not user_profile:
        print("🌟 Welcome to Chatty Patty! 🌟")
        print("Let's create your profile first...")
        app = ProfileSetup()
        app.run()
        
        user_profile = load_user_profile()
        if not user_profile:
            print("❌ Profile creation failed. Exiting...")
            return
    
    print(f"✅ Welcome back {user_profile['username']}!")
    
    local_ip = get_local_ip()
    print(f"🌐 Your IP address: {local_ip}")
    print("🔄 Connecting to central server...")
    
    # Start WebSocket connection in background thread
    start_websocket_connection(user_profile['username'], local_ip)
    
    print("🚀 Loading user directory...")
    app = UserDirectory(user_profile['username'])
    app.run()


if __name__ == "__main__":
    main()