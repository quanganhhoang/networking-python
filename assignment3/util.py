import struct
import time

MAX_BUFFER_SIZE = 16

# return current time
def now():
    return time.ctime(time.time())

# validate expression
# returns true if valid and false otherwise
def validate_expression(expression):
    if not expression:
        return False

    n = len(expression)

    if not expression[0].isdigit() and expression[0] != '+' and expression[0] != '-':
        return False
    
    if (expression[n-1] == '+' or expression[n-1] == '-'): 
        return False

    is_sign = True if expression[0].isdigit() else False
    for i in range(1, n):
        char = expression[i]
        if char == ' ': continue
        if not char.isdigit() and char != '+' and char != '-': # if char not a digit or allowed signs
            return False
        else:
            if (is_sign and char.isdigit()) or (not is_sign and not char.isdigit()): # if expecting a sign but got a digit
                return False
            elif char.isdigit(): # if not expecting a sign and got a digit
                is_sign = True
            elif char == '+' or char == '-': # if expecting a sign and got a sign
                is_sign = False

    return True

# evaluate expression with only numbers and '+' and '-'
def eval(expression):
    if not expression: return 0

    sign = "+"
    num = 0
    stack = []
    for i in range(len(expression)):
        c = expression[i]
        if c.isdigit():
            num = num * 10 + int(c)
        if i == len(expression) - 1 or not c.isdigit():
            if (sign == "+"):
                stack.append(num)
            elif (sign == "-"):
                stack.append(-num)
        
            sign = c
            num = 0
    
    eval = 0
    while (len(stack) != 0):
       eval += stack.pop() 

    return eval

# receive all num_bytes from provided socket
def recv_all(sock, num_bytes):
    total_data = bytearray()
    while len(total_data) < num_bytes:
        remain_bytes = num_bytes - len(total_data)
        bufsize = min(remain_bytes, MAX_BUFFER_SIZE)
        packet = sock.recv(bufsize)
        if not packet:
            return None
        total_data.extend(packet)

    return total_data

# populates an HTML page displaying server stats
def populate_html(eval_expression_stats, get_time_stats, last_ten_expression):
    content = '<!DOCTYPE html><html><body><h1>API count information</h1><h3>/api/evalexpression</h3>'
    content += '<ul>'
    for stat, count in eval_expression_stats.items():
        content += '<li>' + stat + ': ' + str(count) + '</li>'
    content += '</ul>'

    content += '<h3>/api/gettime</h3>'
    content += '<ul>'
    for stat, count in get_time_stats.items():
        content += '<li>' + stat + ': ' + str(count) + '</li>'
    content += '</ul>'

    content += '<h1>Last 10 expressions</h1>'
    content += '<ul>'
    for expression in last_ten_expression:
        content += '<li>' + expression + '</li>'
    content += '</ul></body></html>'

    return content

def generate_res_header(http_version, content_length):
    header = http_version + ' 200 OK\r\n'
    header += 'Content-Type: text/html\r\n'
    header += 'Content-Length: ' + str(content_length) + '\r\n\r\n'
    
    return header


