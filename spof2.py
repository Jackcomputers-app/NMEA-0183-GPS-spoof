import socket
import time

UDP_IP = "192.168.0.255"
# Use "0.255 for the whole network "
UDP_PORT = 5005
SEND_INTERVAL = 0.1  # ~90 Hz

# Default sentence bodies (NO $ and NO *checksum)
DEFAULT_VTG = "GPVTG,,T,,M,,N,,K,N"
DEFAULT_RMC = "GPRMC,125602.3,A,3408.0,N,07752.0,W,5.0,090.0,181225,000.0,E,A"
DEFAULT_GGA = "GPGGA,125602.4,3408.0,N,07752.0,W,1,08,0.9,0.0,M,0.0,M,,"

# Old value "GPRMC,125602.3,V,3408.52882,N,07752.05226,W,,,181225,000.0,E,N"
# old GGA  GPGGA,125602.4,3408.52882,N,07752.05226,W,0,00,,,M,,M,,

def nmea_checksum(body: str) -> str:
    csum = 0
    for ch in body:
        csum ^= ord(ch)
    return f"{csum:02X}"

def make_nmea(body: str) -> bytes:
    body = body.strip()
    cs = nmea_checksum(body)
    return f"${body}*{cs}\r\n".encode("ascii")

def ask_sentence(label: str, default_body: str) -> str:
    print(f"\n{label}")
    print(f"Default: {default_body}*{nmea_checksum(default_body)}")
    user = input("Enter body (or press Enter for default): ").strip()
    return user if user else default_body

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

print("NMEA 0183 UDP Sender (VTG -> RMC -> GGA)")
print("Enter sentence BODY only (no $ and no *checksum).")
print("Press Ctrl+C to stop.\n")
print("Target IP:", UDP_IP, "Target Port:", UDP_PORT)
print("Interval:", SEND_INTERVAL, "seconds\n")

# Ask user (defaults if blank)
vtg_body = ask_sentence("1) GPVTG", DEFAULT_VTG)
rmc_body = ask_sentence("2) GPRMC", DEFAULT_RMC)
gga_body = ask_sentence("3) GPGGA", DEFAULT_GGA)

# Build messages once (fast)
vtg_msg = make_nmea(vtg_body)
rmc_msg = make_nmea(rmc_body)
gga_msg = make_nmea(gga_body)

print("\nSending in order: VTG -> RMC -> GGA (repeating)\n")

try:
    while True:
        sock.sendto(vtg_msg, (UDP_IP, UDP_PORT))
        sock.sendto(rmc_msg, (UDP_IP, UDP_PORT))
        sock.sendto(gga_msg, (UDP_IP, UDP_PORT))

        # Optional: comment this out if printing slows you down at high rates
        print("Sent VTG/RMC/GGA")

        time.sleep(SEND_INTERVAL)

except KeyboardInterrupt:
    print("\nStopped by user.")
finally:
    sock.close()
