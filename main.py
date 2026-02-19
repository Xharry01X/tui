# main.py
import json
import logging
import multiprocessing
import socket
import time

from src.profile_setup import ProfileSetup
from src.users_discovery import UserDirectory
from src.utils import get_local_ip, load_user_profile

SERVER_HOST = "127.0.0.1"
SERVER_PORT = 9999
BUFFER_SIZE = 4096
HEARTBEAT_INTERVAL = 10


def setup_logger(name: str) -> logging.Logger:
    """Configure and return a named logger with a consistent format."""
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            fmt="%(asctime)s [%(name)s] %(levelname)s — %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    logger.setLevel(logging.DEBUG)
    return logger


def tcp_worker_process(username: str, local_ip: str, stop_event: multiprocessing.Event):
    """
    Dedicated OS process — uses a real CPU core, not a thread.
    Connects to the central server via raw TCP, registers the user,
    then loops sending heartbeats until stop_event is set.
    """
    logger = setup_logger(f"TCPWorker[PID={multiprocessing.current_process().pid}]")

    sock = None
    try:
        logger.info("Connecting to %s:%s...", SERVER_HOST, SERVER_PORT)

        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.settimeout(10)  # connection timeout
        sock.connect((SERVER_HOST, SERVER_PORT))
        sock.settimeout(None)  

        logger.info("Connected to central server.")

        registration = (
            json.dumps(
                {
                    "type": "register",
                    "username": username,
                    "ip": local_ip,
                }
            )
            + "\n"
        )

        sock.sendall(registration.encode("utf-8"))
        logger.info("Registered as '%s' @ %s", username, local_ip)

        sock.settimeout(HEARTBEAT_INTERVAL + 2)

        while not stop_event.is_set():
            heartbeat = (
                json.dumps(
                    {
                        "type": "heartbeat",
                        "username": username,
                    }
                )
                + "\n"
            )
            sock.sendall(heartbeat.encode("utf-8"))
            logger.debug("Heartbeat sent.")

            try:
                data = sock.recv(BUFFER_SIZE)
                if not data:
                    logger.warning("Server closed connection.")
                    break
                msg = data.decode("utf-8").strip()
                logger.info("Server says: %s", msg)
            except socket.timeout:
                pass

            for _ in range(HEARTBEAT_INTERVAL):
                if stop_event.is_set():
                    break
                time.sleep(1)

    except ConnectionRefusedError:
        logger.error(
            "Connection refused — is the server running on %s:%s?",
            SERVER_HOST,
            SERVER_PORT,
        )
    except Exception as e:
        logger.exception("Unexpected error: %s", e)
    finally:
        if sock:
            sock.close()
        logger.info("Socket closed. Process exiting.")


def start_tcp_connection(
    username: str, ip: str
) -> tuple[multiprocessing.Process, multiprocessing.Event]:
    """
    Spawns a true OS process (separate CPU core) for the TCP connection.
    Returns (process, stop_event) so the caller can shut it down cleanly.
    """
    logger = logging.getLogger("main")

    stop_event = multiprocessing.Event()

    proc = multiprocessing.Process(
        target=tcp_worker_process,
        args=(username, ip, stop_event),
        name=f"TCPWorker-{username}",
        daemon=True,
    )
    proc.start()
    logger.info("TCP worker process started — PID %s", proc.pid)
    return proc, stop_event


def main():
    multiprocessing.freeze_support()

    logger = setup_logger("main")

    user_profile = load_user_profile()

    if not user_profile:
        logger.info("Welcome to Chatty Patty! Let's create your profile first...")
        app = ProfileSetup()
        app.run()

        user_profile = load_user_profile()
        if not user_profile:
            logger.error("Profile creation failed. Exiting...")
            return

    logger.info("Welcome back, %s!", user_profile["username"])

    local_ip = get_local_ip()
    logger.info("Your IP address: %s", local_ip)
    logger.info("Connecting to central server via raw TCP...")

    tcp_proc, stop_event = start_tcp_connection(user_profile["username"], local_ip)

    try:
        logger.info("Loading user directory...")
        app = UserDirectory(user_profile["username"])
        app.run()
    finally:
        logger.info("Shutting down TCP worker...")
        stop_event.set()
        tcp_proc.join(timeout=5)
        if tcp_proc.is_alive():
            tcp_proc.terminate()
        logger.info("Goodbye!")


if __name__ == "__main__":
    main()
