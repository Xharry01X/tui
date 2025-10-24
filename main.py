# from src.chatty_patty import Chatty
import profile
from src.profile_setup import ProfileSetup
from pathlib import Path
from src.users_discovery import UserDirectory
import json


def main():
    profile_file = Path.home() / ".chatty_patty" / "user_profile.json"
    
    if not profile_file.exists():
        print("🌟 Welcome to Chatty Patty! 🌟")
        print("Let's create your profile first...")
        app = ProfileSetup()
        app.run()
    
    with open(profile_file, 'r') as f:
        profile = json.load(f)
    
    print(f"✅ Welcome back {profile['username']}!")
    print("🚀 Loading user directory...")
    
    app = UserDirectory(profile['username'])
    app.run()


if __name__ == "__main__":
    main()