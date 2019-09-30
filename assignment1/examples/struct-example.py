import struct

expression = b'3+12-7'
encoded_expression = struct.pack('!h6s', len(expression), expression)
print("encoded expression is", encoded_expression)
print("length is", len(encoded_expression))
