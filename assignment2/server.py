import socket
import threading
import struct
import util
import time
import queue

# GLOBAL VARIABLES
is_local = True
NUM_SECONDS_24HR = 60 * 60 * 24

EVAL_API = '/api/evalexpression'
TIME_API = '/api/gettime'
STATUS_API = '/status.html'

LAST_MIN = 'last_min'
LAST_HOUR = 'last_hour'
LAST_24HR = 'last_24HR'
LIFETIME = 'lifetime'

URL = 'url'
REQUEST_TYPE = 'request_type'
HTTP_VERSION = 'http-version'
CONTENT_LENGTH = 'content-length'

times = [0] * NUM_SECONDS_24HR # holds timestamps indexed by time % NUM_SECONDS_24HR
eval_stats = [0] * NUM_SECONDS_24HR
time_stats = [0] * NUM_SECONDS_24HR
last_ten_expression = []

LIFE_TIME_COUNT = [0] * 2 # holds lifetime count for eval_api and time_api

SUPPORTED_ENDPOINT = ['/api/evalexpression', '/api/gettime', '/status.html']
SUPPORTED_HTTP_VERSIONS = ['1.0', '1.1']

# END OF GLOBAL VARIABLES

host_name = socket.getfqdn()
print('hostname is', host_name)

host_ip = socket.gethostbyname('localhost' if is_local else host_name)
print('host IP address is', host_ip)

host_port = 8181

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.bind((host_ip, host_port))
s.listen()
print('Server started. Waiting for connection...')

start_time = int(time.time())

# process each line and save header content into a dict
def process_line(line, line_num, data):
    line = line[:-2] # remove \r\n from string
    print(line)
    if (line_num == 0):
        components = line.split(' ')
        data[REQUEST_TYPE] = components[0]
        data[URL] = components[1]
        data[HTTP_VERSION] = components[2]
    else:
        components = line.split(':')
        data[components[0].lower()] = components[1]

# read header data and saves in a dict
def read_header(sock):
    data = {}
    
    line = bytearray()
    line_num = 0
    while (line != b'\r\n'):
        buf = util.recv_all(sock, 1)
        line.extend(buf)
        if (line != b'\r\n' and line.endswith(b'\n')):
            process_line(line.decode(), line_num, data)
            line_num += 1
            line = bytearray()
    
    return data

# validate request and return status code (404, 400, 200)
def validate_request(request_type, url, http_version, body):
    if (url not in SUPPORTED_ENDPOINT and http_version not in SUPPORTED_HTTP_VERSIONS):
        return '404'
    elif not util.validate_expression(body):
        return '400'
    else:
        return '200'

# process request and return appropriate response
def generate_res_body(url, req_body):
    if (url == EVAL_API):
        last_ten_expression.append(req_body)
        if (len(last_ten_expression) > 10):
            last_ten_expression.pop(0)
        return str(util.eval(req_body))
    elif (url == TIME_API):
        return util.now()
    elif (url == STATUS_API):
        # TODO: init following global variables
        cur_time = int(time.time())
        eval_expression_stats = get_stat(cur_time, EVAL_API)
        get_time_stats = get_stat(cur_time, TIME_API)

        return util.populate_html(eval_expression_stats, get_time_stats, last_ten_expression)

# get current stat for /status.html
def get_stat(cur_time, api):
    data = {LAST_MIN: 0,
            LAST_HOUR: 0,
            LAST_24HR: 0, 
            LIFETIME: LIFE_TIME_COUNT[0] if api == EVAL_API else LIFE_TIME_COUNT[1]}
    
    for i in range(NUM_SECONDS_24HR):
        diff = cur_time - times[i]
        print(diff)
        print(eval_stats[i])
        if diff < 60:
            data[LAST_MIN] += eval_stats[i] if api == EVAL_API else time_stats[i]
        if diff < 60 * 60:
            data[LAST_HOUR] += eval_stats[i] if api == EVAL_API else time_stats[i]
        if diff < NUM_SECONDS_24HR:
            data[LAST_24HR] += eval_stats[i] if api == EVAL_API else time_stats[i]
        
    return data

# update status count per http request
def update_status(url, req_timestamp):
    print('Updating status...\r\n')
    if (url == EVAL_API):
        LIFE_TIME_COUNT[0] += 1
    elif (url == TIME_API):
        LIFE_TIME_COUNT[1] += 1

    index = (req_timestamp - start_time) % NUM_SECONDS_24HR
    
    if (times[index] != req_timestamp):
        times[index] = req_timestamp
        if (url == EVAL_API): 
            eval_stats[index] = 1
        elif (url == TIME_API):
            time_stats[index] = 1
    else:
        if (url == EVAL_API):
            eval_stats[index] += 1
        elif (url == TIME_API):
            time_stats[index] += 1

def process_request(sock):
    header = read_header(sock) # read in header

    req_timestamp = int(time.time()) # take a timestamp

    request_type = header[REQUEST_TYPE]
    url = header[URL]
    http_version = header[HTTP_VERSION]
    
    req_body = ''
    response = ''

    # validate and process request
    if (request_type == 'POST'):
        len_body = int(header[CONTENT_LENGTH])
        req_body = util.recv_all(sock, len_body).decode()
        # print(req_body)
        result = eval(req_body)
        # print(result)
    
    status_code = validate_request(request_type, url, http_version, req_body)
    if (status_code == '404'):
        response = http_version + ' 404\r\n\r\n'
    elif (status_code == '400'):
        response = http_version + ' 400\r\n\r\n'
    else:
        update_status(url, req_timestamp)
        res_body = generate_res_body(url, req_body)
        response = util.generate_res_header(header[HTTP_VERSION], len(res_body)) + res_body

    return response    
    
def handler(conn, addr):
    response = process_request(conn)
    print(response)
    
    conn.sendall(response.encode())

    conn.close()

# main thread
while True:
    client_socket, addr = s.accept()
    print('Server connected by', addr, 'at', util.now())
    threading.Thread(target=handler, args=(client_socket, addr)).start()