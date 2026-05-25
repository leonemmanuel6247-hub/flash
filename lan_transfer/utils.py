import socket
import hashlib
import os

def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
    except Exception:
        ip = "127.0.0.1"
    finally:
        s.close()
    return ip

def file_checksum(filepath):
    h = hashlib.md5()
    with open(filepath, "rb") as f:
        while True:
            chunk = f.read(4096)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()

def format_size(size):
    for u in ["o", "Ko", "Mo", "Go"]:
        if size < 1024:
            return f"{size:.1} {u}"
        size /= 1024
    return f"{size:.1f} To"
