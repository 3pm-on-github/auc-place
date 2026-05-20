import requests
import socket
import threading
import time

server_url = "placeholder"
socket_url = "placeholder"
token = "placeholder"
message_callback = None
socket_thread = None
user = None
passwd = None
shutdown_flag = False
socket_connection = None

# HTTP Section

def sendmsg(msg: str, channel: str = "bots"):
    if token == "placeholder":
        print("Error: Not authenticated")
        return
    try:
        response = requests.post(server_url+"/chat", data=f"{msg}|{channel}|", headers={'Content-Type': 'text/plain', 'auth': token, 'Content-Length': str(len(msg) + 9)}, timeout=1)
        if response.text == "ERR_WHAT_THE_HECK":
            print("Token Expired, getting new token...")
            login(user, passwd, lambda _: None)
            response = requests.post(server_url+"/chat", data=f"{msg}|{channel}|", headers={'Content-Type': 'text/plain', 'auth': token, 'Content-Length': str(len(msg) + 9)}, timeout=1)
    except Exception:
        pass
    print(f"Message sent")

def login(username, password, on_message_callback=None):
    global message_callback, socket_thread, token, user, passwd
    
    message_callback = on_message_callback
    user = username
    passwd = password

    response = requests.post(server_url+"/signup", data=f"{username}|{password}|", headers={'Content-Type': 'text/plain'})
    if response.text == "ERR_USER_USED":
        print("Create account: User already exists, Logging in...")
        response = requests.post(server_url+"/login", data=f"{username}|{password}|", headers={'Content-Type': 'text/plain'})
        token = response.text.split("|")[0]
        print("Login: Success")
        if on_message_callback:
            socket_thread = threading.Thread(target=start_socket, daemon=True)
            socket_thread.start()
            time.sleep(2)
    else:
        token = response.text
        print("Create account: Success")

# Socket Section

def start_socket():
    global socket_connection, shutdown_flag
    hostname = socket_url.replace("http://", "").replace("https://", "").replace("/api", "")
    if ":" in hostname:
        hostname = hostname.split(":")[0]
    
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((hostname, 3033))
    socket_connection = s
    print("Socket connected successfully")
    s.settimeout(1.0)
    
    while not shutdown_flag:
        try:
            data = s.recv(1024)
            if not data:
                break
            message_callback(data.decode())
        except socket.timeout:
            continue
        except Exception:
            break
    
    s.close()

# Miscellanious

def init(url: str):
    global server_url, socket_url
    server_url = url
    socket_url = url.replace("/api", "")

def stop():
    global socket_thread, shutdown_flag, socket_connection
    shutdown_flag = True
    
    if socket_connection:
        try:
            socket_connection.close()
        except:
            pass
    
    if socket_thread and socket_thread != threading.current_thread():
        socket_thread.join()