import os
import subprocess
import sys

directory = os.path.dirname(os.path.abspath(__file__))
bot_path = os.path.join(directory, "simple_csv_bot.py")

if os.name == "nt":
    venv_python = os.path.join(directory, ".venv", "Scripts", "python.exe")
else:
    venv_python = os.path.join(directory, ".venv", "bin", "python")

# Re-launch inside the project's .venv so the right library versions are used.
if os.path.exists(venv_python) and os.path.normcase(os.path.abspath(sys.executable)) != os.path.normcase(venv_python):
    try:
        sys.exit(subprocess.call([venv_python, os.path.abspath(__file__)] + sys.argv[1:]))
    except KeyboardInterrupt:
        sys.exit(0)

import warnings

warnings.filterwarnings("ignore", category=UserWarning)  # harmless urllib3/pkg_resources notices from old libs

import psutil
from telegram import Bot
from telegram.error import Unauthorized

from csv_runtime import get_setting


def stop_existing(script_path):
    current_pid = os.getpid()
    for proc in psutil.process_iter():
        try:
            cmdline = proc.cmdline()
            if proc.pid == current_pid or len(cmdline) < 2:
                continue
            if os.path.normcase(cmdline[1]) == os.path.normcase(script_path):
                proc.terminate()
        except:
            pass


if not get_setting("TOKEN"):
    print("TOKEN is missing. Copy .env.example to .env and put your bot token in it.")
    sys.exit(1)

try:
    me = Bot(get_setting("TOKEN")).get_me()
except Unauthorized:
    print("Telegram rejected the TOKEN in .env (revoked or wrong).")
    print("Get the current one from @BotFather: /mybots -> your bot -> API Token, paste it after TOKEN= in .env.")
    sys.exit(1)

stop_existing(bot_path)
print(f"Bot @{me.username} is running. Press Ctrl+C to stop.")
try:
    sys.exit(subprocess.call([sys.executable, "-W", "ignore::UserWarning", bot_path]))
except KeyboardInterrupt:
    print("Bot stopped.")
