import sys
import os
import subprocess
import time
import signal

BASE = os.path.dirname(os.path.abspath(__file__))
PY = sys.executable


def start_script(script: str, name: str):
    path = os.path.join(BASE, script)
    proc = subprocess.Popen([PY, path], cwd=BASE)
    print(f"[{name}] started pid={proc.pid}")
    return proc


def start_module(module: str, name: str):
    proc = subprocess.Popen([PY, "-m", module], cwd=BASE)
    print(f"[{name}] started pid={proc.pid}")
    return proc


def main():
    procs = []
    procs.append(("bot", start_module("bot.bot", "bot")))
    time.sleep(1.5)
    procs.append(("gui", start_script(os.path.join("gui", "app.py"), "gui")))

    def shutdown(*_):
        print("shutting down...")
        for name, p in procs:
            if p.poll() is None:
                try:
                    p.terminate()
                except Exception:
                    pass
        sys.exit(0)

    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)

    try:
        while True:
            for name, p in list(procs):
                rc = p.poll()
                if rc is not None:
                    print(f"[{name}] exited with code {rc}")
                    if name == "bot":
                        shutdown()
                    else:
                        procs.remove((name, p))
            if not procs:
                break
            time.sleep(1)
    except KeyboardInterrupt:
        shutdown()


if __name__ == "__main__":
    main()
