import os
import time
import socket
import datetime
import subprocess
from pathlib import Path

import paramiko
import pytest

PORT = 2222
HOST = "127.0.0.1"
USERNAME = "admin"
PASSWORD = "password123"
PROMPT_FRAGMENT = "是否繼續並生成表單資料"  # substring to detect


def wait_for_port(host, port, timeout=15.0):
    start = time.time()
    while time.time() - start < timeout:
        try:
            with socket.create_connection((host, port), timeout=1):
                return True
        except OSError:
            time.sleep(0.3)
    return False


def ssh_send_and_collect(channel, send_text, wait_fragment, timeout=20.0):
    channel.send(send_text + "\n")
    buf = ""
    start = time.time()
    while time.time() - start < timeout:
        if channel.recv_ready():
            data = channel.recv(4096).decode(errors="ignore")
            buf += data
            if wait_fragment in buf:
                return buf
        time.sleep(0.25)
    return buf

@pytest.mark.integration
def test_clockmate_llm_flow_shows_generation_prompt():
    # Ensure editable install is done from project root where pyproject.toml exists
    this_file = Path(__file__).resolve()
    root = this_file.parent
    for p in this_file.parents:
        if (p / "pyproject.toml").exists() or (p / "setup.py").exists():
            root = p
            break
    subprocess.check_call(["pip", "install", "-e", "."], cwd=str(root))

    env = os.environ.copy()

    # Start the clockmate SSH server
    server_proc = subprocess.Popen(["clockmate"], env=env)
    try:
        assert wait_for_port(HOST, PORT), "SSH server did not open port 2222 in time"

        # Set up Paramiko SSH client
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(HOST, PORT, username=USERNAME, password=PASSWORD, timeout=10)

        transport = client.get_transport()
        session = transport.open_session()
        session.get_pty()  # request PTY to mimic interactive terminal
        session.invoke_shell()

        # Initial read (banner & prompts)
        initial_buf = ""
        start = time.time()
        while time.time() - start < 10:
            if session.recv_ready():
                initial_buf += session.recv(4096).decode(errors="ignore")
                if ">" in initial_buf:  # user input prompt reached
                    break
            time.sleep(0.25)
        assert ">" in initial_buf, "Did not reach input prompt in initial output:\n" + initial_buf

        # Send user message '今天公出' and await generation prompt
        output_after_message = ssh_send_and_collect(session, "今天公出", PROMPT_FRAGMENT, timeout=30.0)

        assert PROMPT_FRAGMENT in output_after_message, (
            "Did not find generation confirmation prompt. Collected output:\n" + output_after_message
        )

        # Optionally send 'n' to abort and then 'exit' to close
        session.send("n\n")
        time.sleep(0.5)
        session.send("exit\n")
        time.sleep(0.5)

        session.close()
        client.close()
    finally:
        server_proc.terminate()
        try:
            server_proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            server_proc.kill()
