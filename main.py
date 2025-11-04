# from src.chatty_patty import Chatty
import profile
from src.profile_setup import ProfileSetup
from src.users_discovery import UserDirectory
from src.utils import load_user_profile, get_local_ip, register_with_server
import asyncio


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
    asyncio.run(register_with_server(user_profile['username'], local_ip))
    
    print("🚀 Loading user directory...")
    app = UserDirectory(user_profile['username'])
    app.run()


if __name__ == "__main__":
    main()