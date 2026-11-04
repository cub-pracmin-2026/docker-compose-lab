"""Progress of this homework on the class board: what the running app sees about its own setup.

Works only in a Compose container: the board shows the Compose project, that is the folder of the clone, that is
the repo. Until BOARD_ENDS, runs the checks every few seconds and sends each check that passes for the first
time at once; once a minute, sends the time of the last report. BOARD=off in the environment turns it off. A failed
report changes nothing in the API.
"""
import hashlib
import json
import os
import socket
import struct
import threading
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

BOARD_URL = os.environ.get(
    "BOARD_URL", "https://course-leaderboards-default-rtdb.europe-west1.firebasedatabase.app/pm2026/compose")
BOARD_ENDS = datetime(2026, 12, 31, tzinfo=timezone.utc)
CHECK_PERIOD = 2  # seconds: a passed check reaches the board at once
REPORT_PERIOD = 60  # seconds: `seen` and the activity bucket; also the wait after a failed report
SERVER_TIME = {".sv": "timestamp"}
CODE_AT_START = Path("/tmp/cf-finder-code-at-start")

Check = Callable[[], bool]


# ---------- checks of 01-api ----------

def in_container() -> bool:
    return Path("/.dockerenv").exists()


def code_hash() -> str:
    """The hash of the code of the app, as this process of the server loads it."""
    sources = sorted(Path(__file__).parent.glob("*.py"))
    return hashlib.sha256(b"".join(source.read_bytes() for source in sources)).hexdigest()


LOADED_CODE = code_hash()


def docs_written(app) -> bool:
    description = app.openapi()["paths"]["/problems"]["get"].get("description") or ""
    return not description.strip().startswith("TODO")


def code_reloaded() -> bool:
    """The running server has other code than at the start of this container: a code change reached it.

    /tmp lives as long as the container, and a reload or a restart of the container starts a new process of the
    server, which loads the code again. A synced file that no process loaded does not count.
    """
    if not CODE_AT_START.exists():
        CODE_AT_START.write_text(LOADED_CODE)
    return CODE_AT_START.read_text() != LOADED_CODE


def checks_01(app) -> dict[str, Check]:
    return {
        "01-container": in_container,
        "01-docs": lambda: docs_written(app),
        "01-reload": code_reloaded,
    }


# ---------- infrastructure: the repo name and the reports ----------

def skip_name(data: bytes, i: int) -> int:
    """The position after a DNS name that starts at i: labels up to a zero byte, or a pointer."""
    while data[i] != 0:
        if data[i] >= 0xC0:
            return i + 2
        i += data[i] + 1
    return i + 1


def compose_project() -> str | None:
    """Docker DNS names a container <project>-<service>-<n>; Compose names the project after the folder."""
    ip = socket.gethostbyname(socket.gethostname())
    name = ".".join(reversed(ip.split("."))) + ".in-addr.arpa"
    query = struct.pack(">HHHHHH", 0x5043, 0x0100, 1, 0, 0, 0)
    query += b"".join(bytes([len(part)]) + part.encode() for part in name.split(".")) + b"\0"
    query += struct.pack(">HH", 12, 1)  # PTR, IN
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        s.settimeout(2)
        s.sendto(query, ("127.0.0.11", 53))
        answer = s.recv(512)
    if struct.unpack(">H", answer[6:8])[0] == 0:
        return None
    i = skip_name(answer, 12) + 4  # the question: name, type, class
    i = skip_name(answer, i) + 10  # the record: name, type, class, TTL, length; then the name we need
    container = answer[i + 1:i + 1 + answer[i]].decode()
    project, _, _ = container.rpartition("-api-")
    return project or container


def send(method: str, path: str, data) -> int:
    request = urllib.request.Request(f"{BOARD_URL}/{path}.json", json.dumps(data).encode(), method=method,
                                     headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(request, timeout=5) as response:
            return response.status
    except urllib.error.HTTPError as e:
        return e.code


def board_milestones(repo: str) -> set[str]:
    """The checks that the board already has for this repo, from this or an earlier container."""
    try:
        with urllib.request.urlopen(f"{BOARD_URL}/repos/{repo}/milestones.json", timeout=5) as response:
            return set(json.load(response) or {})
    except (OSError, ValueError):
        return set()


def passed(check: Check) -> bool:
    try:
        return bool(check())
    except Exception:  # noqa: BLE001 - a check that cannot run has not passed
        return False


def report(repo: str, new: list[str], sent: set[str]) -> bool:
    """Send `seen`, the activity bucket and the new checks. False when the board did not take all of it."""
    now = datetime.now(timezone.utc)
    bucket = now.strftime("%Y%m%d%H") + str(now.minute // 10)
    ok = send("PATCH", "", {f"repos/{repo}/seen": SERVER_TIME, f"active/{repo}/{bucket}": True}) == 200
    for name in new:
        status = send("PUT", f"repos/{repo}/milestones/{name}", SERVER_TIME)
        if status == 200:
            sent.add(name)
        elif status == 401:
            # The board keeps the first time of each check and refuses a second write. The same 401 comes when the
            # board is closed: then the check is not on the board, and the next report tries again.
            sent |= board_milestones(repo)
            ok = ok and name in sent
        else:
            ok = False
    return ok


def loop(checks: dict[str, Check]) -> None:
    try:
        repo = compose_project()
    except OSError:
        repo = None
    if not repo:
        return
    print(f"Progress of {repo} goes to the class board; BOARD=off turns it off", flush=True)
    sent = board_milestones(repo)
    next_report = 0.0
    while datetime.now(timezone.utc) < BOARD_ENDS:
        new = [name for name, check in checks.items() if name not in sent and passed(check)]
        if new or time.monotonic() >= next_report:
            try:
                ok = report(repo, new, sent)
            except OSError:
                ok = False
            next_report = time.monotonic() + REPORT_PERIOD
            if not ok:
                time.sleep(REPORT_PERIOD)  # the board is down or closed: do not ask it every few seconds
        time.sleep(CHECK_PERIOD)


def start(checks: dict[str, Check]) -> None:
    if os.environ.get("BOARD", "").lower() == "off" or not in_container():
        return
    threading.Thread(target=loop, args=(checks,), daemon=True).start()
