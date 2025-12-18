import socket
import time
import ipaddress

UDP_IP = "192.168.190.144"
UDP_PORT = 5005

def nmea_checksum(body: str) -> str:
    csum = 0
    for ch in body:
        csum ^= ord(ch)
    return f"{csum:02X}"

def make_nmea(body: str) -> bytes:
    cs = nmea_checksum(body)
    return f"${body}*{cs}\r\n".encode("ascii")

def normalize_nmea(line: str) -> bytes:
    line = line.strip()
    if not line:
        return b""
    if line.startswith("$"):
        if not line.endswith("\r\n"):
            line = line + "\r\n"
        return line.encode("ascii", errors="ignore")
    return make_nmea(line)

def ask_ip(default_ip: str) -> str:
    while True:
        ip_str = input(f"Enter target IP address [{default_ip}]: ").strip()
        if not ip_str:
            return default_ip
        try:
            ipaddress.ip_address(ip_str)
            return ip_str
        except ValueError:
            print("Invalid IP address. Please try again.")

def ask_port(default_port: int) -> int:
    while True:
        p = input(f"Enter target UDP port [{default_port}]: ").strip()
        if not p:
            return default_port
        try:
            v = int(p)
            if 1 <= v <= 65535:
                return v
        except ValueError:
            pass
        print("Invalid port. Please try again.")

# Helper: find local IP used to reach destination (to avoid echo)
def get_local_ip_for(dest_ip: str) -> str:
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect((dest_ip, 9))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"

def forward_from_udp(src_host: str, src_port: int, dst_ip: str, dst_port: int, ignore_vtg: bool = True):
    print(f"Listening to UDP NMEA source {src_host}:{src_port} ...")
    recv_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    recv_sock.bind((src_host, src_port))
    recv_sock.settimeout(1.0)  # allow Ctrl+C to interrupt

    udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    local_ip = get_local_ip_for(dst_ip)
    print(f"Forwarding to UDP {dst_ip}:{dst_port}. Press Ctrl+C to stop.")
    print(f"Local IP: {local_ip}")

    try:
        while True:
            try:
                data, addr = recv_sock.recvfrom(4096)
            except socket.timeout:
                continue

            # Avoid echo if we receive our own forwarded packets
            if addr and addr[0] == local_ip:
                continue

            text = data.decode("ascii", errors="ignore")
            for raw in text.splitlines():
                if not raw:
                    continue
                if ignore_vtg and raw.startswith("$GPVTG"):
                    continue  # drop VTG sentences
                msg = normalize_nmea(raw)
                if msg:
                    udp_sock.sendto(msg, (dst_ip, dst_port))
                    print("Sent:", msg.decode(errors="ignore").strip())
    except KeyboardInterrupt:
        print("\nExiting.")
    finally:
        recv_sock.close()
        udp_sock.close()

def main():
    print("NMEA 0183 UDP Forwarder")
    target_ip = ask_ip(UDP_IP)
    target_port = ask_port(UDP_PORT)

    try:
        src_host = input("Source UDP bind address (e.g., 0.0.0.0): ").strip() or "0.0.0.0"
        src_port = int(input("Source UDP port (e.g., 10110): ").strip() or "10110")
        forward_from_udp(src_host, src_port, target_ip, target_port, ignore_vtg=True)
    except Exception as e:
        print("Error:", e)

if __name__ == "__main__":
    main()