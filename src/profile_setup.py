from textual.app import App, ComposeResult
from textual.widgets import Input, Button, Static
from src.utils import get_local_ip, save_user_profile
import asyncio
import threading


class ProfileSetup(App):
    def compose(self) -> ComposeResult:
        yield Static("Create username:")
        yield Input(placeholder="Username", id="username")
        yield Static("", classes="ip-info")
        yield Button("Save", id="save")
        yield Static(id="message")
    
    def on_mount(self):
        local_ip = get_local_ip()
        ip_info = self.query_one(".ip-info")
        ip_info.update(f"Your IP address: {local_ip}")
    
    def on_button_pressed(self, event):
        if event.button.id == "save":
            self.save_profile()
    
    def on_input_submitted(self, event):
        if event.input.id == "username":
            self.save_profile()
    
    def start_websocket_connection(self, username, ip):
        """Start WebSocket connection in background thread"""
        async def keep_alive():
            from src.utils import register_with_server
            await register_with_server(username, ip)
        
        def run_loop():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(keep_alive())
        
        thread = threading.Thread(target=run_loop, daemon=True)
        thread.start()
    
    def save_profile(self):
        username = self.query_one("#username").value.strip()
        if not username:
            self.query_one("#message").update("❌ Please enter a username")
            return
        
        # Save profile locally
        save_user_profile(username)
        local_ip = get_local_ip()
        
        self.query_one("#message").update("🔄 Registering with central server...")
        
        # Start WebSocket connection in background thread
        self.start_websocket_connection(username, local_ip)
        
        self.query_one("#message").update("✅ Profile created! Starting chat...")
        
        # Add small delay to show success message
        self.set_timer(1.5, self.exit)