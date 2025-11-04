from textual.app import App, ComposeResult
from textual.widgets import Input, Button, Static
from textual.containers import Container
from src.utils import load_all_users, get_user_ip_from_server
import asyncio


class ClickableStatic(Static):
    """A clickable Static widget for user selection"""
    
    def on_click(self):
        app = self.app
        if hasattr(app, 'select_user'):
            app.select_user(self.user_data)


class UserDirectory(App):
    def __init__(self, current_username: str):
        super().__init__()
        self.current_user = current_username
        self.users = load_all_users()
        self.selected_user = None
        self.connected_users = {}  
        
    async def get_online_users_once(self):
        """Get online users once when app starts"""
        try:
            # Quick connection just to get current user list
            from src.utils import get_online_users
            online_users = await get_online_users()
            self.connected_users = {user: True for user in online_users}
            self.update_list()
        except:
            pass
    
    def compose(self) -> ComposeResult:
        yield Static(f"Current User: {self.current_user}", id="current-user")
        yield Input(placeholder="Search users...", id="search")
        yield Static("Online Users (click to select):", classes="subtitle")
        yield Container(id="users")
        yield Container(
            Button("Refresh", id="refresh"),
            Button("Get IP", id="get_ip"),
            Button("Chat", id="chat", disabled=True),
            id="action-buttons"
        )
        yield Static("No user selected", id="status")
    
    def on_mount(self):
        # Get online users once on startup (no continuous polling)
        asyncio.create_task(self.get_online_users_once())
        self.update_list()
    
    def refresh_online_status(self):
        """Refresh online status - but don't create persistent connection"""
        asyncio.create_task(self.get_online_users_once())
    
    def update_list(self, search=""):
        users_container = self.query_one("#users")
        users_container.remove_children()
        
        filtered_users = [user for user in self.users if search.lower() in user["username"].lower()]
        
        if not filtered_users and search:
            users_container.mount(Static("No users found", classes="no-users"))
            return
        
        for user in filtered_users:
            is_online = user["username"] in self.connected_users
            status = "🟢 Online" if is_online else "🔴 Offline"
            user_widget = ClickableStatic(f"{user['username']} - {status}")
            user_widget.user_data = user
            user_widget.add_class("user-item")
            
            if self.selected_user and user["username"] == self.selected_user["username"]:
                user_widget.add_class("selected")
            
            users_container.mount(user_widget)
    
    def select_user(self, user_data):
        self.selected_user = user_data
        self.highlight_selected_user()
        self.update_buttons()
        self.update_status()
    
    def highlight_selected_user(self):
        users_container = self.query_one("#users")
        for child in users_container.children:
            if hasattr(child, 'user_data') and child.user_data:
                if child.user_data == self.selected_user:
                    child.add_class("selected")
                else:
                    child.remove_class("selected")
    
    def update_buttons(self):
        chat_button = self.query_one("#chat")
        get_ip_button = self.query_one("#get_ip")
        
        if self.selected_user:
            chat_button.disabled = False
            get_ip_button.disabled = False
        else:
            chat_button.disabled = True
            get_ip_button.disabled = True
    
    def update_status(self):
        status_display = self.query_one("#status")
        if self.selected_user:
            is_online = self.selected_user["username"] in self.connected_users
            status = "Online" if is_online else "Offline"
            ip_info = f" - IP: {self.selected_user.get('ip', 'Unknown')}" if is_online else ""
            status_display.update(f"Selected: {self.selected_user['username']} ({status}{ip_info})")
        else:
            status_display.update("Click on a user to select them")
    
    async def on_button_pressed(self, event):
        if event.button.id == "refresh":
            self.refresh_online_status()
            self.update_list()
            self.notify("User list refreshed")
        
        elif event.button.id == "get_ip":
            if self.selected_user:
                ip = await get_user_ip_from_server(self.selected_user["username"])
                if ip:
                    self.notify(f"IP of {self.selected_user['username']}: {ip}")
                else:
                    self.notify(f"Could not get IP for {self.selected_user['username']}")
        
        elif event.button.id == "chat":
            if self.selected_user:
                self.notify("Chat feature coming soon!")
    
    def on_input_changed(self, event):
        if event.input.id == "search":
            current_search = event.input.value
            self.update_list(current_search)
            
            if self.selected_user:
                filtered_users = [user for user in self.users if current_search.lower() in user["username"].lower()]
                if self.selected_user not in filtered_users:
                    self.selected_user = None
                    self.update_buttons()
                    self.update_status()


# CSS remains the same
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

.ip-info {
    color: $accent;
    padding: 0 1;
}
"""

if __name__ == "__main__":
    app = UserDirectory("current_user")
    app.run()