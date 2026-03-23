"""
ASCII Tag Game — TUI Client

A two-player real-time tag game played over a terminal UI.
Players connect via a WebSocket signaling server, then establish
a direct TCP peer-to-peer connection for low-latency gameplay.

Usage:
    python game_client.py --server ws://localhost:8080

Dependencies:
    pip install textual websockets
"""

import argparse
import asyncio
import json
import logging
import socket
import sys
import time
import traceback
from typing import Optional

logging.basicConfig(
    filename="game_debug.log",
    filemode="w",
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
log = logging.getLogger("game")

try:
    import websockets
    from textual import events
    from textual.app import App, ComposeResult
    from textual.widgets import Static
except ImportError as e:
    sys.exit(f"Missing dep: {e}\n  pip install textual websockets")

GRID_W = 10
GRID_H = 10
SYM_A = "@"
SYM_B = "#"
EMPTY = "."
TICK = 0.12


def render(my_x, my_y, op_x, op_y, am_caller) -> str:
    """
    Build and return a formatted ASCII string representation of the game board.

    Places both players on the grid using their respective symbols, then
    wraps the grid in a border. The caller is always represented by SYM_A
    and the callee by SYM_B, regardless of who is IT.

    Args:
        my_x (int): This player's column position (0-indexed).
        my_y (int): This player's row position (0-indexed).
        op_x (int): Opponent's column position (0-indexed).
        op_y (int): Opponent's row position (0-indexed).
        am_caller (bool): True if this player is the caller (host).

    Returns:
        str: A multi-line ASCII string of the rendered game board.
    """
    grid = [[EMPTY] * GRID_W for _ in range(GRID_H)]
    grid[op_y][op_x] = SYM_B if am_caller else SYM_A
    grid[my_y][my_x] = SYM_A if am_caller else SYM_B
    sep = "+" + "-" * (GRID_W * 2 + 1) + "+"
    return "\n".join([sep] + ["| " + " ".join(r) + " |" for r in grid] + [sep])


def blank_board() -> str:
    """
    Build and return an empty ASCII game board with no players placed.

    Used during non-playing phases (connecting, waiting, end) to show
    the board layout without revealing any position information.

    Returns:
        str: A multi-line ASCII string of an empty bordered grid.
    """
    sep = "+" + "-" * (GRID_W * 2 + 1) + "+"
    return "\n".join(
        [sep] + ["| " + " ".join([EMPTY] * GRID_W) + " |"] * GRID_H + [sep]
    )


def local_ip() -> str:
    """
    Detect and return the machine's primary outbound IPv4 address.

    Opens a temporary UDP socket toward a public DNS server to determine
    which local interface the OS would use for external traffic, then
    reads the bound address without actually sending any data.

    Returns:
        str: The local IPv4 address as a string (e.g. "192.168.1.42").
             Falls back to "127.0.0.1" if detection fails.
    """
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"


class Game(App):  # type: ignore[type-arg]
    """
    Main Textual application class for the ASCII Tag game.

    Manages the full lifecycle of a game session: WebSocket signaling,
    TCP peer-to-peer connection setup, game state, input handling,
    and TUI rendering. The caller acts as the TCP host; the callee
    connects to the caller's advertised address.

    Attributes:
        server (str): WebSocket signaling server URL.
        phase (str): Current game phase — one of: connecting, waiting,
                     matched, playing, end.
        am_caller (bool): True if this client is the signaling caller (host).
        am_it (bool): True if this player is currently "IT" (the chaser).
        my_x / my_y (int): This player's current grid position.
        op_x / op_y (int): Opponent's last known grid position.
        pending_move (str | None): Buffered WASD keypress awaiting next tick.
        status_msg (str): Message shown in the status bar when not playing.
    """

    CSS = """
    Screen  { align: center middle; background: #111; }
    #title  { width: 30; text-align: center; color: yellow; text-style: bold; margin-bottom: 1; }
    #role   { width: 30; text-align: center; color: #88ff88; text-style: bold; }
    #board  { width: 30; color: #ddd; margin-top: 1; margin-bottom: 1; }
    #status { width: 30; text-align: center; color: #aaaaaa; }
    #hint   { width: 30; text-align: center; color: #444444; margin-top: 1; }
    """

    def __init__(self, server: str) -> None:
        """
        Initialise the Game application with the given signaling server URL.

        Args:
            server (str): Full WebSocket URL of the signaling server
                          (e.g. "ws://hurricane:8080").
        """
        super().__init__()
        self.server = server
        self._writer: Optional[asyncio.StreamWriter] = None
        self._reader: Optional[asyncio.StreamReader] = None
        self._recv_task: Optional[asyncio.Task] = None
        self._tick_task: Optional[asyncio.Task] = None

        self.phase = "connecting"
        self.am_caller = False
        self.am_it = False
        self.my_x = self.my_y = 0
        self.op_x = self.op_y = 9
        self.pending_move: Optional[str] = None
        self.status_msg = "Connecting..."

    def compose(self) -> ComposeResult:
        """
        Declare and yield the static TUI widgets that make up the game screen.

        Widgets are stacked vertically: title banner, role indicator,
        game board, status line, and key-hint footer.

        Yields:
            ComposeResult: Sequence of Textual Static widgets.
        """
        yield Static("◈  ASCII TAG  ◈", id="title")
        yield Static("", id="role")
        yield Static(blank_board(), id="board")
        yield Static("Connecting...", id="status")
        yield Static("WASD  move  |  Q quit", id="hint")

    def on_mount(self) -> None:
        """
        Textual lifecycle hook called after the app mounts to the terminal.

        Starts the network worker as an exclusive background task so that
        WebSocket signaling and TCP setup run concurrently with the UI.
        """
        self.run_worker(self._network(), exclusive=True)

    def _refresh(self) -> None:
        """
        Synchronise all TUI widgets with the current game state.

        Updates the role indicator, board grid, and status message based
        on the active phase. During 'playing', the live board and role/IT
        status are rendered; all other phases show a blank board and the
        generic status message.
        """
        board_w = self.query_one("#board", Static)
        status_w = self.query_one("#status", Static)
        role_w = self.query_one("#role", Static)

        if self.phase in ("matched", "playing", "end"):
            my_sym = SYM_A if self.am_caller else SYM_B
            op_sym = SYM_B if self.am_caller else SYM_A
            role_w.update(f"You=[{my_sym}]  Opponent=[{op_sym}]")
        else:
            role_w.update("")

        if self.phase == "playing":
            board_w.update(
                render(self.my_x, self.my_y, self.op_x, self.op_y, self.am_caller)
            )
        else:
            board_w.update(blank_board())

        if self.phase == "playing":
            my_sym = SYM_A if self.am_caller else SYM_B
            op_sym = SYM_B if self.am_caller else SYM_A
            msg = (
                f"[{my_sym}] YOU ARE IT — chase [{op_sym}]!"
                if self.am_it
                else f"[{my_sym}] YOU ARE RUNNER — escape [{op_sym}]!"
            )
            status_w.update(msg)
        else:
            status_w.update(self.status_msg)

    def on_key(self, event: events.Key) -> None:
        """
        Handle keyboard input and buffer the most recent directional key.

        Only WASD keys are accepted and only during the 'playing' phase.
        The move is not applied immediately; it is stored in `pending_move`
        and consumed by the next game tick to enforce a fixed movement rate.

        Args:
            event (events.Key): The Textual key event fired on each keystroke.
        """
        if self.phase != "playing":
            return
        if event.key.lower() in ("w", "a", "s", "d"):
            self.pending_move = event.key.lower()
            log.debug("key buffered: %s  phase=%s", event.key, self.phase)

    async def _game_tick(self) -> None:
        """
        Execute one game tick: apply buffered movement, broadcast position, check win.

        Called every TICK seconds by the tick loop. Consumes the latest
        buffered keypress (if any), clamps the new position to grid bounds,
        sends the updated coordinates to the peer over TCP, and evaluates
        the win condition. The board is re-rendered after each tick.
        """
        if self.phase != "playing":
            return

        mv = self.pending_move
        self.pending_move = None

        if mv:
            dx, dy = {"w": (0, -1), "s": (0, 1), "a": (-1, 0), "d": (1, 0)}[mv]
            nx, ny = self.my_x + dx, self.my_y + dy
            if 0 <= nx < GRID_W and 0 <= ny < GRID_H:
                self.my_x, self.my_y = nx, ny
                log.debug("moved to %d,%d", self.my_x, self.my_y)

        self._refresh()
        self._tcp_send(
            {
                "type": "pos",
                "x": self.my_x,
                "y": self.my_y,
                "t": int(time.time() * 1000),
            }
        )
        self._check_win()

    def _tcp_send(self, obj: dict) -> None:
        """
        Serialise a dictionary to JSON and write it to the peer TCP stream.

        Appends a newline delimiter so the receiver can use readline().
        Schedules an async drain without blocking the caller. Silently
        drops the message if the writer is absent or already closing.

        Args:
            obj (dict): The message payload to serialise and send.
        """
        w = self._writer
        if w is None or w.is_closing():
            return
        try:
            w.write((json.dumps(obj) + "\n").encode())
            t = asyncio.create_task(w.drain())
            t.add_done_callback(lambda _: None)
        except Exception as exc:
            log.warning("_tcp_send: %s", exc)

    def _check_win(self) -> None:
        """
        Evaluate the win condition by comparing both players' grid positions.

        A tag occurs when both players occupy the same cell. If IT reaches
        the runner's cell, IT wins and broadcasts a 'win' message to the
        peer. If the runner lands on IT's cell (edge case), the runner loses
        locally. Transitions the game phase to 'end' on conclusion.
        """
        if self.phase != "playing":
            return
        if self.my_x == self.op_x and self.my_y == self.op_y:
            self.phase = "end"
            if self.am_it:
                self.status_msg = "YOU WIN — opponent caught!"
                self._tcp_send({"type": "win"})
            else:
                self.status_msg = "YOU LOSE — you were caught!"
            self._refresh()

    async def _network(self) -> None:
        """
        Entry point for the background network worker.

        Opens a WebSocket connection to the signaling server and delegates
        all further signaling logic to `_signaling`. Catches and displays
        any unhandled exception, transitioning the game to the 'end' phase
        with an error message.
        """
        try:
            async with websockets.connect(
                self.server, ping_interval=None, ping_timeout=None
            ) as ws:
                log.debug("ws connected")
                await self._signaling(ws)
        except Exception as exc:
            log.error("_network: %s\n%s", exc, traceback.format_exc())
            self.phase = "end"
            self.status_msg = f"Error: {exc}"
            self._refresh()

    async def _signaling(self, ws) -> None:
        """
        Process all WebSocket signaling messages from the server.

        Handles the full pre-game handshake sequence:
          - 'waiting'       — server queuing this client for a match.
          - 'matched'       — pair found; role (caller/callee) assigned.
          - 'ice-candidate' — caller's TCP address relayed to the callee.
          - 'peer-left'     — opponent disconnected; award win by default.

        The caller proceeds to `_host()` to open a TCP server; the callee
        proceeds to `_join()` once the host address is received.

        Args:
            ws: An open websockets connection to the signaling server.
        """
        async for raw in ws:
            msg = json.loads(raw)
            kind = msg.get("type")
            log.debug("ws ← %s", kind)

            if kind == "waiting":
                self.phase = "waiting"
                self.status_msg = "Waiting for opponent..."
                self._refresh()

            elif kind == "matched":
                self.am_caller = msg["role"] == "caller"
                self.phase = "matched"
                my_sym = SYM_A if self.am_caller else SYM_B
                op_sym = SYM_B if self.am_caller else SYM_A
                self.status_msg = f"Matched! You=[{my_sym}] Opp=[{op_sym}]"
                self._refresh()

                if self.am_caller:
                    await self._host(ws)

            elif kind == "ice-candidate":
                if not self.am_caller:
                    ip = msg.get("ip", "127.0.0.1")
                    port = int(msg.get("port", 0))
                    log.debug("callee: got tcp addr %s:%d", ip, port)
                    self.status_msg = f"Connecting to host..."
                    self._refresh()
                    await self._join(ip, port)

            elif kind == "peer-left":
                if self.phase != "end":
                    self.phase = "end"
                    self.status_msg = "Opponent left — you win!"
                    self._refresh()
                break

    async def _host(self, ws) -> None:
        """
        Open an ephemeral TCP server, advertise its address, and await the peer.

        Binds a TCP listener on all interfaces at an OS-assigned port, then
        relays the detected public IP and port to the callee via the signaling
        channel using an 'ice-candidate' message. Waits up to 15 seconds for
        the callee to connect before timing out. On a successful connection,
        closes the listening server and proceeds to `_start_game`.

        Args:
            ws: An open websockets connection used to send the address relay.
        """
        log.debug("host: starting TCP server")
        connected: asyncio.Future = asyncio.get_event_loop().create_future()

        async def _accept(r: asyncio.StreamReader, w: asyncio.StreamWriter) -> None:
            log.debug("host: client connected from %s", w.get_extra_info("peername"))
            self._reader, self._writer = r, w
            if not connected.done():
                connected.set_result(True)

        srv = await asyncio.start_server(_accept, "0.0.0.0", 0)
        port = srv.sockets[0].getsockname()[1]
        ip = local_ip()
        log.debug("host: listening on %s:%d", ip, port)

        await ws.send(json.dumps({"type": "ice-candidate", "ip": ip, "port": port}))
        self.status_msg = f"Waiting for opponent to connect (:{port})..."
        self._refresh()

        try:
            await asyncio.wait_for(connected, timeout=15.0)
        except asyncio.TimeoutError:
            self.phase = "end"
            self.status_msg = "Timeout — opponent never connected."
            self._refresh()
            return

        srv.close()
        await self._start_game()

    async def _join(self, ip: str, port: int) -> None:
        """
        Attempt to establish a TCP connection to the caller's game server.

        Retries up to 7 times with a 400 ms delay between attempts to
        accommodate network latency or the host not yet being ready.
        On success, delegates immediately to `_start_game`. On total
        failure, transitions the game to the 'end' phase with an error.

        Args:
            ip (str): IPv4 address of the caller's TCP server.
            port (int): Port number of the caller's TCP server.
        """
        for attempt in range(1, 8):
            try:
                log.debug("join: attempt %d → %s:%d", attempt, ip, port)
                r, w = await asyncio.wait_for(
                    asyncio.open_connection(ip, port), timeout=3.0
                )
                self._reader, self._writer = r, w
                log.debug("join: connected!")
                await self._start_game()
                return
            except Exception as exc:
                log.warning("join attempt %d failed: %s", attempt, exc)
                self.status_msg = f"Connecting... (attempt {attempt})"
                self._refresh()
                await asyncio.sleep(0.4)

        self.phase = "end"
        self.status_msg = "Could not reach host."
        self._refresh()

    async def _start_game(self) -> None:
        """
        Perform the pre-game READY handshake and initialise gameplay for both peers.

        Both the caller and callee execute this identical code path:
          1. Send a 'ready' message over TCP.
          2. Block until a 'ready' message is received from the peer.
          3. Assign starting positions (caller: top-left, callee: bottom-right).
          4. Set the 'playing' phase and spawn the tick and receive tasks.

        The caller starts as IT; the callee starts as the runner.
        Both background tasks are held as instance attributes to prevent
        premature garbage collection by the asyncio event loop.
        """
        log.debug("_start_game: sending READY")
        self._tcp_send({"type": "ready"})

        reader = self._reader
        assert reader is not None
        try:
            while True:
                line = await asyncio.wait_for(reader.readline(), timeout=10.0)
                if not line:
                    raise ConnectionError("peer closed before READY")
                m = json.loads(line.decode().strip())
                if m.get("type") == "ready":
                    log.debug("_start_game: peer READY received")
                    break
        except Exception as exc:
            log.error("_start_game READY handshake: %s", exc)
            self.phase = "end"
            self.status_msg = f"Handshake failed: {exc}"
            self._refresh()
            return

        self.am_it = self.am_caller
        if self.am_caller:
            self.my_x, self.my_y = 0, 0
            self.op_x, self.op_y = 9, 9
        else:
            self.my_x, self.my_y = 9, 9
            self.op_x, self.op_y = 0, 0

        self.phase = "playing"
        self._refresh()
        log.debug(
            "game started: am_it=%s pos=(%d,%d)", self.am_it, self.my_x, self.my_y
        )

        self._tick_task = asyncio.create_task(self._run_tick())
        self._tick_task.add_done_callback(
            lambda t: (
                log.error("tick task died: %s", t.exception())
                if t.exception()
                else None
            )
        )

        self._recv_task = asyncio.create_task(self._recv_loop())
        self._recv_task.add_done_callback(
            lambda t: (
                log.error("recv task died: %s", t.exception())
                if t.exception()
                else None
            )
        )

    async def _run_tick(self) -> None:
        """
        Drive the game tick loop at a fixed interval until the game ends.

        Sleeps for TICK seconds between iterations, then calls `_game_tick`
        to process input, broadcast position, and check the win condition.
        Exits automatically when the phase leaves 'playing'.
        """
        log.debug("_run_tick started")
        while self.phase == "playing":
            await asyncio.sleep(TICK)
            await self._game_tick()
        log.debug("_run_tick ended (phase=%s)", self.phase)

    async def _recv_loop(self) -> None:
        """
        Continuously read and process incoming TCP messages from the peer.

        Runs for the duration of the 'playing' phase. Each newline-delimited
        JSON message is parsed and dispatched:
          - 'pos' — updates the opponent's coordinates and re-renders the board.
          - 'win' — peer has caught this player; transitions to 'end' as a loss.

        A 5-second readline timeout is used to keep the loop responsive to
        phase changes without blocking indefinitely. Handles peer disconnection
        and unexpected exceptions, always cleaning up the phase on exit.
        """
        log.debug("_recv_loop started")
        reader = self._reader
        if reader is None:
            return
        try:
            while self.phase == "playing":
                try:
                    line = await asyncio.wait_for(reader.readline(), timeout=5.0)
                except asyncio.TimeoutError:
                    continue
                if not line:
                    log.debug("_recv_loop: peer closed")
                    break
                try:
                    m = json.loads(line.decode().strip())
                except Exception:
                    continue

                t = m.get("type")
                if t == "pos":
                    self.op_x, self.op_y = int(m["x"]), int(m["y"])
                    self._check_win()
                    if self.phase == "playing":
                        self._refresh()
                elif t == "win":
                    log.debug("received win from peer")
                    self.phase = "end"
                    self.status_msg = "YOU LOSE — opponent caught you!"
                    self._refresh()
                    break

        except Exception as exc:
            log.error("_recv_loop: %s\n%s", exc, traceback.format_exc())
        finally:
            if self.phase == "playing":
                self.phase = "end"
                self.status_msg = "Connection lost."
                self._refresh()
            log.debug("_recv_loop ended")


def _port_open(ip: str, port: int, timeout: float = 0.3) -> bool:
    """Return True if a TCP connection to ip:port succeeds within timeout."""
    try:
        s = socket.create_connection((ip, port), timeout=timeout)
        s.close()
        return True
    except OSError:
        return False


def _subnet_scan(port: int) -> Optional[str]:
    """
    Scan every host on the local /24 subnet for an open port.

    Derives the subnet from the machine's own outbound IP, then probes
    all 254 host addresses concurrently using threads. Returns the first
    IP that responds, or None if none do.

    Args:
        port (int): TCP port to probe on each host.

    Returns:
        Optional[str]: First responding IP address, or None.
    """
    my_ip = local_ip()
    prefix = ".".join(my_ip.split(".")[:3])
    log.debug("subnet_scan: probing %s.1-254:%d", prefix, port)
    print(f"  Scanning {prefix}.0/24 for port {port}...", flush=True)

    found: list = []

    def probe(i: int) -> None:
        ip = f"{prefix}.{i}"
        if ip != my_ip and _port_open(ip, port):
            found.append(ip)

    import concurrent.futures
    with concurrent.futures.ThreadPoolExecutor(max_workers=64) as ex:
        list(ex.map(probe, range(1, 255)))

    if found:
        log.debug("subnet_scan: found %s", found[0])
        return found[0]
    return None


def resolve_server(url: str) -> str:
    """
    Resolve the signaling server URL, auto-discovering the IP if needed.

    Tries each strategy in order and returns the first URL that leads to
    a reachable host:

      1. Original URL as-is (hostname may resolve via DNS / hosts file).
      2. mDNS variant — appends '.local' to the hostname, which works on
         Windows when Bonjour / Apple services are installed.
      3. Subnet scan — probes every address on the local /24 for the port,
         no configuration required.

    Exits with an error only if all three strategies fail.

    Args:
        url (str): WebSocket URL supplied by the user or default, e.g.
                   "ws://hurricane:8080".

    Returns:
        str: A working WebSocket URL with a numeric or resolvable host.
    """
    import urllib.parse
    parsed = urllib.parse.urlparse(url)
    host = parsed.hostname or ""
    port = parsed.port or 8080

    # 1. Try as-is
    try:
        infos = socket.getaddrinfo(host, port)
        ip = infos[0][4][0]
        if _port_open(ip, port):
            log.debug("resolve_server: '%s' resolved and reachable", host)
            return url
        log.debug("resolve_server: '%s' resolves but port %d closed", host, port)
    except socket.gaierror:
        log.debug("resolve_server: '%s' DNS failed, trying mDNS", host)

    # 2. Try mDNS  (<hostname>.local — works on Windows with Bonjour)
    mdns_host = f"{host}.local"
    try:
        infos = socket.getaddrinfo(mdns_host, port)
        ip = infos[0][4][0]
        if _port_open(ip, port):
            mdns_url = url.replace(f"://{host}:", f"://{mdns_host}:", 1)
            log.debug("resolve_server: mDNS hit → %s", mdns_url)
            print(f"  Found server via mDNS: {mdns_host}", flush=True)
            return mdns_url
    except socket.gaierror:
        log.debug("resolve_server: mDNS '%s' also failed, trying subnet scan", mdns_host)

    # 3. Subnet scan
    print(f"  Hostname '{host}' not resolvable — auto-discovering server...", flush=True)
    found_ip = _subnet_scan(port)
    if found_ip:
        discovered_url = url.replace(f"://{host}", f"://{found_ip}", 1)
        log.debug("resolve_server: subnet scan → %s", discovered_url)
        print(f"  Server found at {found_ip}", flush=True)
        return discovered_url

    print(
        f"\nCould not find the signaling server on the local network.\n"
        f"Make sure the server is running and on the same Wi-Fi/LAN.\n"
    )
    sys.exit(1)


def main() -> None:
    """
    Parse command-line arguments and launch the ASCII Tag game application.

    Accepts an optional --server flag to override the default signaling
    server URL. Initialises and runs the Textual Game app, which blocks
    until the user quits (Q key or terminal close).

    CLI Args:
        --server (str): WebSocket URL of the signaling server.
                        Defaults to "ws://hurricane:8080".
    """
    ap = argparse.ArgumentParser(description="ASCII Tag Game")
    ap.add_argument("--server", default="ws://hurricane:8080", metavar="URL")
    args = ap.parse_args()
    server_url = resolve_server(args.server)
    log.debug("=== start server=%s ===", server_url)
    Game(server_url).run()


if __name__ == "__main__":
    main()