from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Input, Header, Footer, Static, Button
from textual import on
from datetime import datetime


class Chatty(App):
    CSS = """
    Screen {
        background: $surface;
    }
    
    Header {
        background: $accent;
        color: $text;
        text-style: bold;
    }
    
    .message-left {
        background: $success 10%;
        border-left: heavy $success;
        margin: 1;
        padding: 1;
    }
    
    .message-right {
        background: $primary 10%;
        border-right: heavy $primary;
        margin: 1;
        padding: 1;
        text-align: right;
    }
    
    #chat-container {
        height: 1fr;
        layout: vertical;
    }

    #chat-title {
        height: auto;
        text-align: center;
    }

    #chat-messages {
        height: 1fr;
        border: solid $primary;
        overflow: auto;
    }

    #input-container {
        height: auto;
        layout: horizontal;
    }
    """

    BINDINGS = [("ctrl+c", "quit", "Exit")]

    def __init__(self):
        super().__init__()
        self.messages = []
        self.current_user = "You"
        self.other_user = "Other User"

    def compose(self) -> ComposeResult:
        """Create the application UI layout"""
        yield Header()
        with Vertical(id="chat-container"):
            yield Container(id="chat-messages")
        with Horizontal(id="input-container"):
            yield Input(placeholder="Type your message...", id="message-input")
            yield Button("Send", id="send-button")
        yield Footer()

    def on_mount(self) -> None:
        """Set up the initial state of the application"""
        self.title = "Chatty Patty"

    def add_message(self, user: str, message: str) -> None:
        """Add a message to the chat"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.messages.append((user, message, timestamp))
        self.update_messages()

    def update_messages(self) -> None:
        messages_container = self.query_one("#chat-messages")
        messages_container.remove_children()

        for sender, message, timestamp in self.messages:
            message_class = "message-right" if sender == self.current_user else "message-left"

            message_widget = Static(
                f"[{timestamp}] {sender}: {message}",
                classes=message_class
            )
            messages_container.mount(message_widget)
        
        messages_container.scroll_end()

    @on(Input.Submitted, "#message-input")
    @on(Button.Pressed, "#send-button")
    def send_message(self) -> None:
        input_widget = self.query_one("#message-input")
        message = input_widget.value.strip()
        if message:
            self.add_message(self.current_user, message)
            input_widget.value = ""
            self.auto_respond(message)

    def auto_respond(self, message: str) -> None:
        """Automatically respond to the user's message"""
        if not message.strip():
            return
        user_message_lower = message.lower()
        if "hello" in user_message_lower:
            response = "Hi there! How can I help you today?"
        elif "how are you" in user_message_lower:
            response = "I'm just a computer program, but thanks for asking!"
        elif "bye" in user_message_lower:
            response = "Goodbye! Have a great day!"
        else:
            response = "I'm not sure what you mean. Can you please rephrase?"
        
        self.call_later(self.add_message, self.other_user, response)
