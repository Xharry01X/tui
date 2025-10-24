from textual.app import App, ComposeResult
from textual.widgets import Input, Button, Static
from pathlib import Path
import json
from datetime import datetime


class ProfileSetup(App):
    def compose(self) -> ComposeResult:
        yield Static("Create username:")
        yield Input(placeholder="Username", id="username")
        yield Button("Save", id="save")
        yield Static(id="message")
    
    def on_button_pressed(self, event):
        if event.button.id == "save":
            username = self.query_one("#username").value.strip()
            if not username:
                self.query_one("#message").update("Enter username")
                return
            
            profile_dir = Path.home() / ".chatty_patty"
            profile_dir.mkdir(exist_ok=True)
            
            profile = {
                "username": username,
                "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "last_seen": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "is_online": True
            }
            
            with open(profile_dir / "user_profile.json", "w") as f:
                json.dump(profile, f, indent=2)
            
            # Add to all users
            users_file = profile_dir / "all_users.json"
            users = []
            if users_file.exists():
                with open(users_file, 'r') as f:
                    users = json.load(f)
            
            if not any(u['username'] == username for u in users):
                users.append(profile)
                with open(users_file, 'w') as f:
                    json.dump(users, f, indent=2)
            
            self.exit()
    
    def on_input_submitted(self, event):
        if event.input.id == "username":
            self.query_one("#save").press()