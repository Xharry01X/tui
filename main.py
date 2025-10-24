# from src.chatty_patty import Chatty
import profile
from src.profile_setup import ProfileSetup
from pathlib import Path
import json


def main():
    profile_file = Path.home() / ".chatty_patty" / "user_profile.json"
    if not profile_file.exists():
        app = ProfileSetup()
        app.run()
    else:
        with open(profile_file, 'r') as f:
            profile = json.load(f)
        print(f"Welcome back {profile['username']}!")
        print("Online users: Checking...")


if __name__ == "__main__":
    main()