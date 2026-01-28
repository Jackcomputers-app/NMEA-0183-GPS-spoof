import socket

# Configuration
UDP_IP = "192.168.190.144"  # Target IP address (localhost for testing)
UDP_PORT = 5005       # Target port
MESSAGE = b"Hello, World! \n" # Inorder to send data 

#When 0138 message ends must end a cl 

print(f"UDP target IP: {UDP_IP}")
print(f"UDP target port: {UDP_PORT}")
print(f"Message: {MESSAGE}")


# Create a socket object
# socket.AF_INET specifies the address family (IPv4)
# socket.SOCK_DGRAM specifies that this is a UDP socket
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# Send the message to the specified address and port
sock.sendto(MESSAGE, (UDP_IP, UDP_PORT))

# Optional: Close the socket (though not strictly necessary for simple sends in UDP)
sock.close()
