import socket
import time
import ipaddress

UDP_IP = "192.168.0.203"
UDP_PORT = 5005
SEND_INTERVAL = 0.01111  # seconds (1/90 second)

def nmea_checksum(body: str) -> str:
    csum = 0
    for ch in body:
        csum ^= ord(ch)
    return f"{csum:02X}"

def make_nmea(body: str) -> bytes:
    cs = nmea_checksum(body)
    return f"$${body}*{cs}\r\n".encode("ascii")

# Create UDP socket
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

print("NMEA 0183 UDP Sender (10 Hz)")
print("Enter sentence body only (no $ or *)")
print("Example:")
print("  GPRMC,031407.0,V,3851.33300,N,09447.94100,W,,,070717,000.0,E,N")
print("Press Ctrl+C to stop\n")
print("Target IP:", UDP_IP, "Target Port:", UDP_PORT)

# Ask once
body = input("NMEA sentence > ").strip()
if not body:
    print("No sentence entered, exiting.")
    exit(1)

msg = make_nmea(body)

print("\nSending every 0.1 seconds...\n")

try:
    while True:
        sock.sendto(msg, (UDP_IP, UDP_PORT))
        print("Sent:", msg.decode().strip())
        time.sleep(SEND_INTERVAL)

except KeyboardInterrupt:
    print("\nStopped by user.")

finally:
    sock.close()
