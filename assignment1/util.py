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
    while (len(total_data) < num_bytes):
        packet = sock.recv(num_bytes - len(total_data))
        if not packet:
            return None
        total_data.extend(packet)

    return total_data