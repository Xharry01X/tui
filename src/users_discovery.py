from textual.app import App, ComposeResult
from textual.widgets import Input, Button, Static
from textual.containers import Container
from pathlib import Path
import json
import random
from datetime import datetime, timedelta


class ClickableStatic(Static):
    """A clickable Static widget for user selection"""
    
    def on_click(self):
        # Get the main app instance and call its select_user method
        app = self.app
        if hasattr(app, 'select_user'):
            app.select_user(self.user_data)


class UserDirectory(App):
    def __init__(self, current_username: str):
        super().__init__()
        self.current_user = current_username
        self.users_file = Path.home() / ".chatty_patty" / "all_users.json"
        self.users = []
        self.selected_user = None  # Track selected user
        self.load_or_create_users()
    
    def load_or_create_users(self):
        if self.users_file.exists():
            with open(self.users_file, 'r') as f:
                self.users = json.load(f)
        else:
            self.users = [
                {"username": "alice", "last_seen": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "is_online": True},
                {"username": "bob", "last_seen": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "is_online": False},
                {"username": "charlie", "last_seen": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "is_online": True},
            ]
            self.save_users()
    
    def save_users(self):
        self.users_file.parent.mkdir(exist_ok=True)
        with open(self.users_file, 'w') as f:
            json.dump(self.users, f, indent=2)
    
    def compose(self) -> ComposeResult:
        yield Static(f"Current User: {self.current_user}", id="current-user")
        yield Input(placeholder="Search users...", id="search")
        yield Static("Click on any user below to select them:", classes="subtitle")
        yield Container(id="users")
        yield Container(  # Container for action buttons
            Button("Refresh", id="refresh"),
            Button("Add User", id="add", classes="hidden"),  # Initially hidden
            Button("Chat", id="chat", disabled=True),  # Initially disabled
            id="action-buttons"
        )
        yield Static("No user selected", id="status")
    
    def on_mount(self):
        self.update_list()
    
    def update_list(self, search=""):
        users_container = self.query_one("#users")
        users_container.remove_children()
        
        filtered_users = [user for user in self.users if search.lower() in user["username"].lower()]
        
        if not filtered_users and search:
            users_container.mount(Static("No users found", classes="no-users"))
            return
        
        for user in filtered_users:
            status = "🟢 Online" if user["is_online"] else "🔴 Offline"
            user_widget = ClickableStatic(f"{user['username']} - {status}")
            user_widget.user_data = user  # Store user data in the widget
            user_widget.add_class("user-item")
            
            # Highlight if this is the selected user
            if self.selected_user and user["username"] == self.selected_user["username"]:
                user_widget.add_class("selected")
            
            users_container.mount(user_widget)
    
    def select_user(self, user_data):
        """Handle user selection"""
        self.selected_user = user_data
        self.highlight_selected_user()
        self.update_buttons()
        self.update_status()
    
    def highlight_selected_user(self):
        """Highlight the selected user and remove highlights from others"""
        users_container = self.query_one("#users")
        for child in users_container.children:
            if hasattr(child, 'user_data') and child.user_data:
                if child.user_data == self.selected_user:
                    child.add_class("selected")
                else:
                    child.remove_class("selected")
    
    def update_buttons(self):
        """Update button states based on selection"""
        add_button = self.query_one("#add")
        chat_button = self.query_one("#chat")
        
        if self.selected_user:
            # Show Add User button and enable Chat button
            add_button.remove_class("hidden")
            chat_button.disabled = False
        else:
            # Hide Add User button and disable Chat button
            add_button.add_class("hidden")
            chat_button.disabled = True
    
    def update_status(self):
        """Update the status display"""
        status_display = self.query_one("#status")
        if self.selected_user:
            status = "Online" if self.selected_user["is_online"] else "Offline"
            status_display.update(f"Selected: {self.selected_user['username']} ({status})")
        else:
            status_display.update("Click on a user to select them")
    
    def on_button_pressed(self, event):
        if event.button.id == "refresh":
            # Clear selection when refreshing
            self.selected_user = None
            for user in self.users:
                if user["username"] != self.current_user:
                    user["is_online"] = random.choice([True, False])
                    user["last_seen"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.save_users()
            self.update_list()
            self.update_buttons()
            self.update_status()
        
        elif event.button.id == "add":
            if self.selected_user:
                self.notify(f"Added user: {self.selected_user['username']} to contacts")
        
        elif event.button.id == "chat":
            if self.selected_user:
                self.notify("Chat feature coming soon!")
    
    def on_input_changed(self, event):
        """Handle search input changes"""
        if event.input.id == "search":
            current_search = event.input.value
            self.update_list(current_search)
            
            # If we have a selected user but it's not in the current search results, clear selection
            if self.selected_user:
                filtered_users = [user for user in self.users if current_search.lower() in user["username"].lower()]
                if self.selected_user not in filtered_users:
                    self.selected_user = None
                    self.update_buttons()
                    self.update_status()


# Add CSS for styling
UserDirectory.CSS = """
#current-user {
    text-style: bold;
    background: $primary;
    color: $background;
    padding: 1;
    text-align: center;
}

.subtitle {
    padding: 1;
    text-style: italic;
}

#users {
    height: 50%;
    border: solid $accent;
    margin: 1;
    overflow-y: auto;
}

.user-item {
    padding: 1;
}

.user-item:hover {
    background: $accent 30%;
    color: $text;
}

.selected {
    background: $accent;
    color: $primary;
    text-style: bold;
}

.hidden {
    display: none;
}

#action-buttons {
    layout: horizontal;
    height: auto;
    margin: 1;
}

#action-buttons > Button {
    width: 1fr;
    margin: 0 1;
}

#status {
    background: $panel;
    padding: 1;
    text-align: center;
}

.no-users {
    padding: 2;
    text-align: center;
    text-style: italic;
}

Button:disabled {
    opacity: 0.5;
}
"""

if __name__ == "__main__":
    app = UserDirectory("current_user")
    app.run()