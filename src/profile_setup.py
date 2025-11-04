from textual.app import App, ComposeResult
from textual.widgets import Input, Button, Static
from src.utils import get_local_ip, save_user_profile, register_with_server
import asyncio


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
    
    def save_profile(self):
        username = self.query_one("#username").value.strip()
        if not username:
            self.query_one("#message").update("❌ Please enter a username")
            return
        
        save_user_profile(username)
        
        self.query_one("#message").update("🔄 Registering with central server...")
        
        async def register():
            local_ip = get_local_ip()
            success = await register_with_server(username, local_ip)
            if success:
                self.query_one("#message").update("✅ Profile created and registered with server!")
            else:
                self.query_one("#message").update("✅ Profile created (server offline)")
            self.exit()

        asyncio.run(register())