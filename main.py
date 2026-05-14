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
        userdata[user] = {"pixelsleft": 25, "maxcharges": 25, "droplets": 50, "speed": 1} # default max at 25.

    # Commands
    if message.startswith("a/p uptime"):
        api.sendmsg(f"been running since {UPSINCE[:10]} at {UPSINCE[11:19]} UTC")
    elif message.startswith("a/p ping"):
        api.sendmsg("pong!")
    elif message.startswith("a/p help"):
        api.sendmsg("available commands: a/p uptime, a/p ping, a/p help, a/p place, a/p grid, a/p mypixels, a/p bulkplace, a/p status, a/p droplets, a/p shop, a/p buy\nthere's a maximum of 25 pixel charges for every user. a pixel is given to everyone every 5 seconds.\nthe max charge is increased for everyone every minute.")
    elif message == "a/p status":
        pixelcount = sum(1 for row in grid for cell in row if cell != "FFFFFF")
        api.sendmsg(f"Grid size: {len(grid)}x{len(grid[0])}\nUser data: {len(userdata)} users\nPixels placed: {pixelcount}")
    elif message == "a/p mypixels":
        api.sendmsg(f"{user} has {userdata[user]['pixelsleft']}/{userdata[user]['maxcharges']} pixels left")
    
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
        userdata[user]["droplets"] += 1
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
        userdata[user]["droplets"] += width * height
        api.sendmsg(f"{user} placed {color} at {x}, {y} with size {width}x{height}")
        
    elif message.startswith("a/p grid"):
        jsontopng.convert()
        link = upload_image("grid.png")
        api.sendmsg(f"grid uploaded to {link}")
        os.remove("grid.png")
    
    # Droplets part
    elif message.startswith("a/p droplets"):
        api.sendmsg(f"{user} has {userdata[user]['droplets']} droplets")
    elif message == "a/p shop":
        api.sendmsg("--- Shop ---\n1. a/p buy [amount] [pixels/maxcharges] / Buys more pixels or max charges.\nPrice: 2 droplets per pixel, 10 droplets per max charge\n2. a/p buy [amount] speed / Buys a speed boost to get more pixels/maxcharges \nPrice: 15 droplets per speed boost")
    elif message.startswith("a/p buy"):
        parts = message.removeprefix("a/p buy").strip().split(" ")
        if len(parts) != 2:
            api.sendmsg("Usage: a/p buy [amount] [pixels/maxcharges/speed]")
            return
        amount = int(parts[0])
        item = parts[1]
        if item == "pixels":
            if userdata[user]["droplets"] < amount * 2:
                api.sendmsg(f"{user} does not have enough droplets")
                return
            userdata[user]["droplets"] -= amount * 2
            userdata[user]["pixelsleft"] += amount
        elif item == "maxcharges":
            if userdata[user]["droplets"] < amount * 10:
                api.sendmsg(f"{user} does not have enough droplets")
                return
            userdata[user]["droplets"] -= amount * 10
            userdata[user]["maxcharges"] += amount
        elif item == "speed":
            if userdata[user]["droplets"] < amount * 15:
                api.sendmsg(f"{user} does not have enough droplets")
                return
            userdata[user]["droplets"] -= amount * 15
            userdata[user]["speed"] += amount
        with open("db/userdata.json", "w") as f:
            json.dump(userdata, f)
        api.sendmsg(f"{user} bought {amount} {item}")

def givepixels():
    timeelapsed = 0
    while True:
        timeelapsed += 5
        if timeelapsed == 60:
            timeelapsed = 0
            for user in userdata:
                userdata[user]["maxcharges"] += userdata[user]["speed"]

        for user in userdata:
            if userdata[user]["pixelsleft"] < userdata[user]["maxcharges"]:
                userdata[user]["pixelsleft"] += userdata[user]["speed"]
            userdata[user]["droplets"] += userdata[user]["speed"]*5
        with open("db/userdata.json", "w") as f:
            json.dump(userdata, f)
        time.sleep(5)

def cli_input_loop():
    while True:
        try:
            user_input = input("CLI >>> ").strip()
            if user_input.lower() in ["exit", "quit"]:
                print("Exiting CLI...")
                break
            elif user_input.startswith("sendacmsg "):
                api.sendmsg(user_input.replace("sendacmsg ", ""))
            elif user_input.startswith("givepixels"):
                user_input_parts = user_input.split(" ")
                user = user_input_parts[1]
                amount = int(user_input_parts[2])
                if user not in userdata:
                    print(f"User {user} not found")
                    continue
                if amount + userdata[user]["pixelsleft"] >= userdata[user]["maxcharges"]:
                    userdata[user]["pixelsleft"] = userdata[user]["maxcharges"]
                else:
                    userdata[user]["pixelsleft"] += amount
                with open("db/userdata.json", "w") as f:
                    json.dump(userdata, f)
                print(f"Gave {user} {amount} pixels")
            elif user_input.startswith("givemaxcharges"):
                user_input_parts = user_input.split(" ")
                user = user_input_parts[1]
                amount = int(user_input_parts[2])
                if user not in userdata:
                    print(f"User {user} not found")
                    continue
                userdata[user]["maxcharges"] += amount
                with open("db/userdata.json", "w") as f:
                    json.dump(userdata, f)
                print(f"Gave {user} {amount} max charges")
            elif user_input.startswith("givedroplets"):
                user_input_parts = user_input.split(" ")
                user = user_input_parts[1]
                amount = int(user_input_parts[2])
                if user not in userdata:
                    print(f"User {user} not found")
                    continue
                userdata[user]["droplets"] += amount
                with open("db/userdata.json", "w") as f:
                    json.dump(userdata, f)
                print(f"Gave {user} {amount} droplets")
        except (KeyboardInterrupt, EOFError):
            api.stop()
            break

# bot init
api.init(API_URL)
api.login(USERNAME, PASSWORD, on_message_callback=on_message)
print("Bot is running...")
api.sendmsg("auc/place is online!")
threading.Thread(target=givepixels).start()
threading.Thread(target=cli_input_loop).start()
try:
    while True:
        time.sleep(0.1)
except KeyboardInterrupt:
    print("Shutting down...")
    api.stop()