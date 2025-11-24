#!/usr/bin/env python3
import sys
import json
import traceback

def err(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)

def send(obj):
    print(json.dumps(obj, ensure_ascii=False), flush=True)

def main():
    err("stdio test server started", flush=True)
    try:
        while True:
            line = sys.stdin.readline()
            if line == "":
                err("stdin EOF -> exiting")
                break
            line = line.strip()
            if not line:
                continue
            err("RECV:", line)
            try:
                data = json.loads(line)
            except Exception:
                err("invalid json received:", line)
                continue

            # Example: respond to initialize request
            if data.get("type") == "initialize" or data.get("method") == "initialize":
                resp = {
                    "type": "initialize_result",
                    "capabilities": {"example": True},
                    "id": data.get("id", "init"),
                }
                send(resp)
                continue

            # generic ack
            send({"type": "ack", "received": data})
    except Exception:
        err("Unhandled exception:\n" + traceback.format_exc())
        sys.exit(1)

if __name__ == "__main__":
    main()