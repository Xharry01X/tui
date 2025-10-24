from textual.app import App, ComposeResult
from textual.widgets import Input, Button, Static
from textual.containers import Center
from textual import events
from pathlib import Path
import json
from datetime import datetime


class ProfileSetup(App):
    def compose(self) -> ComposeResult:
        yield Center(Static("Create Your Chat Profile", id="title"))
        yield Center(Input(placeholder="Enter username", id="username"))
        yield Center(Button("Save Profile", id="save"))
        yield Static(id="message")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "save":
            username_input = self.query_one("#username")
            username = username_input.value.strip()

            if not username:
                self.query_one("#message").update("Please enter a username.")
                return

            profile_dir = Path.home() / ".chatty_patty"
            profile_dir.mkdir(exist_ok=True)
            
            profile = {
                "username": username,
                "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }

            with open(profile_dir / "user_profile.json", "w") as f:
                json.dump(profile, f)

            self.query_one("#message").update("Profile saved successfully.")
            self.call_later(self.exit)