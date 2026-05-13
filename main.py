import datetime
import api
import os
import json
import time
import jsontopng
import requests
import threading
from dotenv import load_dotenv

load_dotenv()
IP = "104.236.25.60"
API_URL = f"http://{IP}:6767/api"
PORT = 3033
USERNAME = "auc/place"
PASSWORD = os.getenv("AUC_PASSWORD")
UPSINCE = datetime.datetime.now(tz=datetime.timezone.utc).isoformat()
grid = [["FFFFFF"] * 1024 for _ in range(1024)]
userdata = {}

# DB Initialization
def createDB():
    print("Creating database files...")
    with open("db/grid.json", "w") as f:
        json.dump(grid, f)
    with open("db/userdata.json", "w") as f:
        json.dump({}, f)
if not os.path.exists("db/grid.json") or not os.path.exists("db/userdata.json"):
    createDB()
else:
    with open("db/grid.json", "r") as f:
        grid = json.load(f)
    with open("db/userdata.json", "r") as f:
        userdata = json.load(f)

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
    if user not in userdata:
        userdata[user] = {"pixelsleft": 25} # maxes out at 25.

    # Commands
    if message.startswith("a/p uptime"):
        api.sendmsg(f"been running since {UPSINCE[:10]} at {UPSINCE[11:19]} UTC")
    elif message.startswith("a/p ping"):
        api.sendmsg("pong!")
    elif message.startswith("a/p help"):
        api.sendmsg("available commands: a/p uptime, a/p ping, a/p help, a/p place, a/p grid, a/p mypixels, a/p bulkplace, a/p status\nthere's a maximum of 25 pixel charges for every user. a pixel is given to everyone every 5 seconds.")
    elif message == "a/p status":
        api.sendmsg(f"Grid size: {len(grid)}x{len(grid[0])}")
        api.sendmsg(f"User data: {len(userdata)} users")
    elif message == "a/p mypixels":
        api.sendmsg(f"{user} has {userdata[user]['pixelsleft']} pixels left")
    
    # Placing part
    elif message.startswith("a/p place"):
        if userdata[user]["pixelsleft"] <= 0:
            api.sendmsg(f"{user} has no pixels left")
            return
        userdata[user]["pixelsleft"] -= 1
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
    elif message.startswith("a/p bulkplace"):
        # TODO: implement bulk placing
        parts = message.removeprefix("a/p bulkplace").strip().split(" ")
        if len(parts) != 5:
            api.sendmsg("Usage: a/p bulkplace <x> <y> <width> <height> <color in hex>")
            return
        x = int(parts[0])
        y = int(parts[1])
        width = int(parts[2])
        height = int(parts[3])
        color = parts[4].lstrip("#").upper()
        if width * height > userdata[user]["pixelsleft"]:
            api.sendmsg(f"{user} does not have enough pixels")
            return
        userdata[user]["pixelsleft"] -= width * height
        for i in range(width):
            for j in range(height):
                grid[y + j][x + i] = color
        with open("db/grid.json", "w") as f:
            json.dump(grid, f)
        api.sendmsg(f"{user} placed {color} at {x}, {y} with size {width}x{height}")
        
    elif message.startswith("a/p grid"):
        jsontopng.convert()
        link = upload_image("grid.png")
        api.sendmsg(f"grid uploaded to {link}")
        os.remove("grid.png")

def givepixels():
    while True:
        for user in userdata:
            if userdata[user]["pixelsleft"] < 25:
                userdata[user]["pixelsleft"] += 1
        with open("db/userdata.json", "w") as f:
            json.dump(userdata, f)
        time.sleep(5)

# bot init
api.init(API_URL)
api.login(USERNAME, PASSWORD, on_message_callback=on_message)
print("Bot is running...")
api.sendmsg("auc/place is online!")
threading.Thread(target=givepixels).start()
try:
    while True:
        time.sleep(0.1)
except KeyboardInterrupt:
    print("Shutting down...")
    api.stop()