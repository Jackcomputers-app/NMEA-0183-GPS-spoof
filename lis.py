import socket

# Define the IP and port you want to listen on
UDP_IP = "0.0.0.0"  # Listen on all available interfaces
UDP_PORT = 5005

# Create a UDP socket
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# Bind the socket to the address and port
sock.bind((UDP_IP, UDP_PORT))

print(f"Listening for UDP packets on {UDP_IP}:{UDP_PORT}...")

try:
    while True:
        # Receive message from the socket
        data, addr = sock.recvfrom(1024)  # Buffer size is 1024 bytes
        print(f"Received message: {data} from {addr}")

except KeyboardInterrupt:
    print("\nProgram interrupted. Exiting gracefully...")
    sock.close()
