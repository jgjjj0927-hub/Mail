import sys
import os
import subprocess

BASE = os.path.dirname(os.path.abspath(__file__))


def run_gui():
    subprocess.run([sys.executable, os.path.join(BASE, "gui", "app.py")], check=True)


def run_bot():
    subprocess.run([sys.executable, os.path.join(BASE, "bot", "bot.py")], check=True)


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "gui"
    if mode == "gui":
        run_gui()
    elif mode == "bot":
        run_bot()
    else:
        print("usage: python main.py [gui|bot]")
