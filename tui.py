from textual.app import App, ComposeResult
from textual.widgets import Static, Header, Footer
from textual.containers import Container
import psutil
import time

class NetworkMonitor(App):
    """A simple network speed and WiFi monitor."""
    
    CSS = """
    Container {
        layout: vertical;
        padding: 1;
    }
    
    .stats {
        padding: 1;
        border: solid green;
        margin: 1;
    }
    
    .title {
        text-style: bold;
        background: blue;
        color: white;
        padding: 1;
        text-align: center;
    }
    """
    
    def compose(self) -> ComposeResult:
        yield Header()
        yield Container(
            Static("📊 NETWORK MONITOR", classes="title"),
            Static(id="network_stats"),
            Static(id="wifi_info"),
            Static(id="connection_stats"),
        )
        yield Footer()
    
    def on_mount(self) -> None:
        """Set up periodic updates when app starts."""
        self.set_interval(1, self.update_stats)
        self.last_bytes_sent = psutil.net_io_counters().bytes_sent
        self.last_bytes_recv = psutil.net_io_counters().bytes_recv
        self.last_time = time.time()
    
    def update_stats(self) -> None:
        """Update network statistics."""
        # Network speed calculation
        current_bytes_sent = psutil.net_io_counters().bytes_sent
        current_bytes_recv = psutil.net_io_counters().bytes_recv
        current_time = time.time()
        
        time_diff = current_time - self.last_time
        upload_speed = (current_bytes_sent - self.last_bytes_sent) / time_diff
        download_speed = (current_bytes_recv - self.last_bytes_recv) / time_diff
        
        interfaces = psutil.net_if_addrs()
        stats = psutil.net_if_stats()
        
        active_interface = None
        for interface, addrs in interfaces.items():
            if stats[interface].isup and interface != 'lo':  # Skip loopback
                active_interface = interface
                break
        
        
        wifi_info = "Not available"
        if active_interface:
            if 'wireless' in active_interface.lower() or 'wifi' in active_interface.lower() or 'wlan' in active_interface:
                wifi_info = f"📶 WiFi: {active_interface} - Connected"
            else:
                wifi_info = f"🔗 Wired: {active_interface} - Connected"
        
        
        def format_speed(speed):
            if speed > 1000000:  # > 1 MB
                return f"{speed/1000000:.1f} MB/s"
            elif speed > 1000:   # > 1 KB
                return f"{speed/1000:.1f} KB/s"
            else:
                return f"{speed:.1f} B/s"
        
        network_stats = f"📡 NETWORK SPEED: Upload: {format_speed(upload_speed)} Download: {format_speed(download_speed)}"
        
        connection_stats = f"🔌 CONNECTION INFO: Interface: {active_interface or 'Not found'} Status: {'Connected' if active_interface else 'Disconnected'}"
        
        self.query_one("#network_stats").update(network_stats)
        self.query_one("#wifi_info").update(wifi_info)
        self.query_one("#connection_stats").update(connection_stats)
        
        self.last_bytes_sent = current_bytes_sent
        self.last_bytes_recv = current_bytes_recv
        self.last_time = current_time

if __name__ == "__main__":
    app = NetworkMonitor()
    app.run(host="0.0.0.0", port=8023)