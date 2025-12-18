import socket
import time
import math
from datetime import datetime, timezone

UDP_IP = "192.168.0.255"     # broadcast for 192.168.0.0/24
UDP_PORT = 5005
SEND_INTERVAL = 1.0          # 1 Hz is realistic for NMEA (you can change)

START_LAT_DDM = 3408.08333   # 34°08.08333'  (DDMM.MMMMM)
START_LAT_NS  = "N"
START_LON_DDM = 7752.00000   # 077°52.00000' (DDDMM.MMMMM) -> NOTE: numeric stored without leading zero
START_LON_EW  = "W"

def nmea_checksum(body: str) -> str:
    csum = 0
    for ch in body:
        csum ^= ord(ch)
    return f"{csum:02X}"

def make_nmea(body: str) -> bytes:
    body = body.strip()
    cs = nmea_checksum(body)
    return f"${body}*{cs}\r\n".encode("ascii")

def ddmm_to_decimal_lat(ddmm: float, ns: str) -> float:
    dd = int(ddmm // 100)
    mm = ddmm - dd * 100
    dec = dd + (mm / 60.0)
    if ns.upper() == "S":
        dec = -dec
    return dec

def dddmm_to_decimal_lon(dddmm: float, ew: str) -> float:
    ddd = int(dddmm // 100)
    mm = dddmm - ddd * 100
    dec = ddd + (mm / 60.0)
    if ew.upper() == "W":
        dec = -dec
    return dec

def decimal_to_ddmm_lat(lat_dec: float):
    ns = "N" if lat_dec >= 0 else "S"
    lat_dec = abs(lat_dec)
    dd = int(lat_dec)
    mm = (lat_dec - dd) * 60.0
    ddmm = dd * 100 + mm
    return f"{ddmm:09.5f}", ns  # DDMM.MMMMM (width includes leading 0 if needed)

def decimal_to_dddmm_lon(lon_dec: float):
    ew = "E" if lon_dec >= 0 else "W"
    lon_dec = abs(lon_dec)
    ddd = int(lon_dec)
    mm = (lon_dec - ddd) * 60.0
    dddmm = ddd * 100 + mm
    return f"{dddmm:010.5f}", ew  # DDDMM.MMMMM

def utc_hhmmss_s():
    now = datetime.now(timezone.utc)
    return now.strftime("%H%M%S") + f".{int(now.microsecond/100000):1d}"

def utc_ddmmyy():
    now = datetime.now(timezone.utc)
    return now.strftime("%d%m%y")

def triangle_wave(t: float, period: float) -> float:
    """
    Returns a triangle wave in range [-1, +1] with given period (seconds).
    """
    x = (t % period) / period  # 0..1
    if x < 0.25:
        return 4 * x
    elif x < 0.75:
        return 2 - 4 * x
    else:
        return -4 + 4 * x

def main():
    print("NMEA 0183 UDP Sender (Moving North/South)")
    try:
        amp_nm = float(input("How many NM up/down from start? (default 5): ").strip() or "5")
    except ValueError:
        amp_nm = 5.0

    try:
        period_sec = float(input("Seconds for a full up+down cycle? (default 120): ").strip() or "120")
    except ValueError:
        period_sec = 120.0

    # Convert start to decimal degrees
    start_lat = ddmm_to_decimal_lat(START_LAT_DDM, START_LAT_NS)
    start_lon = dddmm_to_decimal_lon(START_LON_DDM, START_LON_EW)

    # 1 NM = 1 minute of latitude = 1/60 degree
    amp_deg_lat = amp_nm / 60.0

    # Triangle wave gives constant speed segments; compute approximate speed from amplitude+period
    # Over half-cycle (period/2), it goes from -amp to +amp => distance 2*amp_nm over period/2 hours
    # speed_knots = distance_nm / hours
    speed_knots = (2 * amp_nm) / ((period_sec / 2) / 3600.0)

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

    print(f"\nBroadcasting to {UDP_IP}:{UDP_PORT}")
    print(f"Amplitude: ±{amp_nm} NM, Period: {period_sec}s, Approx speed: {speed_knots:.1f} kn")
    print("Ctrl+C to stop.\n")

    t0 = time.time()

    try:
        while True:
            t = time.time() - t0
            w = triangle_wave(t, period_sec)  # -1..+1

            lat = start_lat + (amp_deg_lat * w)
            lon = start_lon  # keep longitude fixed for “up/down” movement

            lat_str, ns = decimal_to_ddmm_lat(lat)
            lon_str, ew = decimal_to_dddmm_lon(lon)

            # Course: if moving north (wave increasing), COG ~ 000; if moving south, ~180
            # Use derivative sign from triangle wave segments:
            phase = (t % period_sec) / period_sec
            moving_north = (phase < 0.25) or (phase >= 0.75)  # rising segments in our triangle_wave
            cog = 0.0 if moving_north else 180.0

            hhmmss = utc_hhmmss_s()
            ddmmyy = utc_ddmmyy()

            # VTG (course+speed)
            vtg_body = f"GPVTG,{cog:.1f},T,,M,{speed_knots:.1f},N,{speed_knots*1.852:.1f},K,A"

            # RMC (status A, speed+course included)
            rmc_body = f"GPRMC,{hhmmss},A,{lat_str},{ns},{lon_str},{ew},{speed_knots:.1f},{cog:.1f},{ddmmyy},000.0,E,A"

            # GGA (fix quality 1, 8 sats, hdop 0.9, alt 0)
            gga_body = f"GPGGA,{hhmmss},{lat_str},{ns},{lon_str},{ew},1,08,0.9,0.0,M,0.0,M,,"

            sock.sendto(make_nmea(vtg_body), (UDP_IP, UDP_PORT))
            sock.sendto(make_nmea(rmc_body), (UDP_IP, UDP_PORT))
            sock.sendto(make_nmea(gga_body), (UDP_IP, UDP_PORT))

            print(f"LAT {lat_str}{ns}  LON {lon_str}{ew}  COG {cog:5.1f}  SOG {speed_knots:5.1f}", end="\r")

            time.sleep(SEND_INTERVAL)

    except KeyboardInterrupt:
        print("\nStopped by user.")
    finally:
        sock.close()

if __name__ == "__main__":
    main()
