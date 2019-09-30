# This example is using Python 3.
import socket
import struct
from util import recv_all

is_local = True
# Specify server name and port number to connect to.
#
# API: getfqdn()
#   returns a fully qualified domain name.
server_name = 'localhost' if is_local else socket.getfqdn()
print('Hostname: ', server_name)
server_port = 8181

# Make a TCP socket object.
#
# API: socket(address_family, socket_type)
#
# Address family
#   AF_INET: IPv4
#   AF_INET6: IPv6
#
# Socket type
#   SOCK_STREAM: TCP socket
#   SOCK_DGRAM: UDP socket
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Connect to server machine and port.
#
# API: connect(address)
#   connect to a remote socket at the given address.
s.connect((server_name, server_port))
print('Connected to server ', server_name)

# messages to send to server.
messages = ['3+12-7', '2+3-5', '2-3-5', '2', '4']
encoded_expression = struct.pack('!h', len(messages))

for msg in messages:
    encoded_expression += struct.pack('!h' + str(len(msg)) + 's', len(msg), msg.encode("utf-8"))

print(encoded_expression)

# Send messages to server over socket.
#
# API: send(bytes)
#   Sends data to the connected remote socket.  Returns the number of
#   bytes sent. Applications are responsible for checking that all
#   data has been sent
#
# API: recv(bufsize)
#   Receive data from the socket. The return value is a bytes object
#   representing the data received. The maximum amount of data to be
#   received at once is specified by 'bufsize'.
#
# API: sendall(bytes)
#   Sends data to the connected remote socket.  This method continues
#   to send data from string until either all data has been sent or an
#   error occurs.

# bufsize = 1024
# for line in message:
#   s.sendall(str.encode(line, 'utf-8'))
#   data = s.recv(bufsize)
#   print('Client received: ', data)

s.sendall(encoded_expression)

bufsize = 16

num_answers = recv_all(s, 2)
# response.extend(num_answers)

for i in range(len(messages)):
    result_len = recv_all(s, 2)
    # response.extend(result_len)
    response = messages[i]
    response += " = "
    response += recv_all(s, int.from_bytes(result_len, 'big')).decode("utf-8")
    print(response)

# Close socket to send EOF to server.
s.close()
