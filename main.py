import datetime
import api
import os
import json
import time
import jsontopng
import requests
from dotenv import load_dotenv

load_dotenv()
IP = "104.236.25.60"
API_URL = f"http://{IP}:6767/api"
PORT = 3033
USERNAME = "auc/place"
PASSWORD = os.getenv("AUC_PASSWORD")
UPSINCE = datetime.datetime.now(tz=datetime.timezone.utc).isoformat()
grid = [["FFFFFF"] * 1024 for _ in range(1024)]

# DB Initialization
def createDB():
    print("Creating database files...")
    with open("db/grid.json", "w") as f:
        json.dump(grid, f)
    with open("db/userdata.json", "w") as f:
        json.dump({}, f)
if not os.path.exists("db/grid.json") or not os.path.exists("db/userdata.json"):
    createDB()

# Image Uploading
def upload_image(file_path):
    with open(file_path, "rb") as f:
        response = requests.post(
            "https://tmpfiles.org/api/v1/upload",
            files={"file": f},
            timeout=5
        )
    data = response.json()
    if data.get("status") == "success":
        url = data["data"]["url"]
        direct_url = url.replace("tmpfiles.org/", "tmpfiles.org/dl/")
        print("URL:", direct_url)
        return direct_url
    else:
        raise Exception("Upload failed:", data)

def on_message(originalmsg):
    # Parsing
    print(f"Bot received: {originalmsg}")
    message = originalmsg.split("|")[1]
    user = originalmsg.split("|")[0]
    if originalmsg.startswith("auroracross|"):
        user = message.split(": ", 1)[0].removeprefix("from ") if ": " in message else user
        message = message.split(": ", 1)[1] if ": " in message else message
    if originalmsg.startswith("auc/place|"):
        return
    
    # Commands
    if message.startswith("a/p uptime"):
        api.sendmsg(f"been running since {UPSINCE[:10]} at {UPSINCE[11:19]} UTC")
    elif message.startswith("a/p ping"):
        api.sendmsg("pong!")
    elif message.startswith("a/p help"):
        api.sendmsg("available commands: a/p uptime, a/p ping, a/p help, a/p place, a/p grid")
    elif message.startswith("a/p place"):
        parts = message.removeprefix("a/p place").strip().split(" ")
        if len(parts) != 3:
            api.sendmsg("Usage: a/p place <x> <y> <color in hex>")
            return
        x = int(parts[0])
        y = int(parts[1])
        color = parts[2].lstrip("#").upper()
        grid[y][x] = color
        with open("db/grid.json", "w") as f:
            json.dump(grid, f)
        api.sendmsg(f"{user} placed {color} at {x}, {y}")
    elif message.startswith("a/p grid"):
        jsontopng.convert()
        link = upload_image("grid.png")
        api.sendmsg(f"grid uploaded to {link}")
        os.remove("grid.png")
    elif message.startswith("a/p "):
        api.sendmsg("Unknown command")

# bot init
api.init(API_URL)
api.login(USERNAME, PASSWORD, on_message_callback=on_message)
print("Bot is running...")
api.sendmsg("auc/place is online!")
try:
    while True:
        time.sleep(0.1)
except KeyboardInterrupt:
    print("Shutting down...")
    api.stop()