import socket
import threading
import time
import struct

import config
import util

is_local = True

host_name = socket.getfqdn()
print('hostname is', host_name)

host_ip = socket.gethostbyname('localhost' if is_local else host_name)
print('host IP address is', host_ip)

host_port = config.EXPRESSION_EVAL_PORT

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.bind((host_ip, host_port))
s.listen()
print('Server started. Waiting for connection...')

def now():
    return time.ctime(time.time())

def handler(conn, addr):
    expression = ""
    num_expressions = 0
    expression_len = 0
    response = bytearray()

    data = util.recv_all(conn, 2) # get number of expressions to process
    
    num_expression = int.from_bytes(data, 'big')
    print(f'Processing {num_expression} expressions sent from client...')
    response.extend(struct.pack('!h', num_expression))

    for i in range(num_expression):
        expression_len = int.from_bytes(util.recv_all(conn, 2), 'big')
        expression = util.recv_all(conn, expression_len).decode("utf-8")
        result = str(util.eval(expression)) # evaluate the expression and return a string representation
        response.extend(struct.pack('!h' + str(len(result)) + 's', len(result), result.encode("utf-8")))
        print(expression + " = " + str(util.eval(expression)))
    
    print("Sending back results...")
    conn.sendall(response)
        # print('Server received:', data, 'from', addr)
        # conn.sendall(str.encode('Echo ==> ') + data)
        # time.sleep(10)  # simulating long running program
    conn.close()

# main thread
while True:
    client_socket, addr = s.accept()
    print('Server connected by', addr, 'at', now())
    threading.Thread(target=handler, args=(client_socket, addr)).start()