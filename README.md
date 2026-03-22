# ◈ ASCII TAG ◈

A two-player real-time **terminal tag game** built with Python, Textual, and WebSockets.
Players connect through a central signaling server, then battle it out over a direct
peer-to-peer TCP connection — no server middleman once the game starts.

```
+---------------------+
| . . . . . . . . . . |
| . @ . . . . . . . . |   @ = IT (chaser)
| . . . . . . . . . . |   # = Runner
| . . . . . . . . . . |
| . . . . . # . . . . |
+---------------------+
     [#] YOU ARE RUNNER — escape [@]!
```

---

## Features

- 🎮 Real-time 10×10 grid gameplay at 120 ms ticks
- 🔗 WebSocket-based matchmaking and signaling
- 🤝 Direct TCP peer-to-peer connection (no relay after match)
- 🖥️ Modern terminal UI powered by [Textual](https://textual.textualize.io/)
- ⚡ Buffered input system — smooth movement even under lag
- 🏷️ Automatic role assignment: caller = IT, callee = runner
- 🔄 Retry logic for NAT traversal (7 connection attempts)
- 📋 Full debug logging to `game_debug.log`

---

## How It Works

```
Player A                  Signaling Server              Player B
   │                            │                           │
   │──── connect (WS) ─────────►│◄──── connect (WS) ───────│
   │◄─── role: "caller" ────────│──── role: "callee" ──────►│
   │                            │                           │
   │─── ice-candidate ──────────►──── ip:port relay ───────►│
   │                            │                           │
   │◄══════════════ TCP direct P2P connection ══════════════►│
   │                            │                           │
   │◄──────────────── READY handshake (TCP) ───────────────►│
   │                                                         │
   │◄═══════════════ pos / win messages (TCP) ══════════════►│
```

1. Both players connect to the **WebSocket signaling server**.
2. The server pairs them and assigns roles — **caller** (host) and **callee** (joiner).
3. The caller opens a TCP server and relays its `ip:port` via the signaling channel.
4. The callee connects directly to that TCP address — signaling is no longer used.
5. Both peers exchange a `READY` handshake, then the game loop begins.

---

## Prerequisites

- Python **3.8+**
- pip packages: `textual`, `websockets`
- A running **WebSocket signaling server** on `ws://localhost:8080`
  (or any compatible server at a custom URL)

---

## Installation

```bash
# 1. Clone the repository
git clone https://github.com/yourusername/ascii-tag.git
cd ascii-tag

# 2. Install dependencies
pip install textual websockets
```

---

## Usage

### Start the game client

```bash
# Connect to the default local signaling server
python main.py

# Connect to a custom signaling server
python main.py --server ws://your-server.com:8080
```

### Controls

| Key | Action         |
|-----|----------------|
| `W` | Move up        |
| `A` | Move left      |
| `S` | Move down      |
| `D` | Move right     |
| `Q` | Quit the game  |

### Gameplay

- The **caller** (first to connect) starts at position `(0, 0)` and is **IT**.
- The **callee** (second to connect) starts at `(9, 9)` and is the **runner**.
- IT must move onto the runner's tile to win.
- The runner must survive and avoid being caught.

---

## Project Structure

```
ascii-tag/
├── main.py          # Full game client — TUI, networking, game logic
├── game_debug.log   # Auto-generated debug log (created at runtime)
└── README.md        # This file
```

### Key components inside `main.py`

| Component        | Description                                                  |
|------------------|--------------------------------------------------------------|
| `render()`       | Builds the ASCII board string from current player positions  |
| `blank_board()`  | Returns an empty board for non-playing phases                |
| `local_ip()`     | Detects the machine's outbound IPv4 for TCP advertisement    |
| `Game` (App)     | Main Textual app — owns all state, UI, and networking        |
| `_network()`     | Background worker — manages WebSocket lifecycle              |
| `_signaling()`   | Processes all pre-game WS messages (waiting/matched/left)    |
| `_host()`        | Caller path — opens TCP server, waits for peer               |
| `_join()`        | Callee path — retries TCP connection to caller               |
| `_start_game()`  | READY handshake + spawns tick and recv tasks for both peers  |
| `_game_tick()`   | Per-tick: apply move → send pos → check win                  |
| `_recv_loop()`   | Reads peer TCP stream; handles `pos` and `win` messages      |
| `_check_win()`   | Tags occur when both players share the same grid cell        |

---

## Configuration

These constants at the top of `main.py` control game behaviour:

| Constant  | Default | Description                          |
|-----------|---------|--------------------------------------|
| `GRID_W`  | `10`    | Board width in cells                 |
| `GRID_H`  | `10`    | Board height in cells                |
| `TICK`    | `0.12`  | Seconds per game tick (120 ms)       |
| `SYM_A`   | `@`     | Symbol for the caller (IT)           |
| `SYM_B`   | `#`     | Symbol for the callee (runner)       |

---

## Debugging

A full debug log is written to `game_debug.log` in the working directory on every run.
It captures connection attempts, role assignments, position updates, task lifecycle
events, and any errors from the network or game loops.

```bash
tail -f game_debug.log   # live-tail while the game is running
```

---

## Building a Standalone Executable

```bash
pip install pyinstaller
pyinstaller --onefile --name AsciiTag main.py
```

The binary will be placed in the `dist/` directory.

---

## Dependencies

| Package     | Purpose                                |
|-------------|----------------------------------------|
| `textual`   | Terminal UI framework (widgets, CSS)   |
| `websockets`| Async WebSocket client for signaling   |

---

## Roadmap

- [ ] Configurable grid size via CLI flags
- [ ] Scoreboard and round counter
- [ ] Spectator mode via signaling server
- [ ] NAT hole-punching for wider P2P compatibility
- [ ] Sound effects via terminal bell sequences

---

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/my-feature`)
3. Commit your changes (`git commit -m 'Add my feature'`)
4. Push to the branch (`git push origin feature/my-feature`)
5. Open a Pull Request

---

## License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.

---

*Built with ❤️ using Python, Textual, and raw TCP sockets.*
