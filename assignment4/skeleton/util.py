import dummy
import gbn
import sw
import struct


def get_transport_layer_by_name(name, local_port, remote_port, msg_handler):
  assert name == 'dummy' or name == 'sw' or name == 'gbn'
  if name == 'dummy':
    return dummy.DummyTransportLayer(local_port, remote_port, msg_handler)
  if name == 'sw':
    return sw.StopAndWait(local_port, remote_port, msg_handler)
  if name == 'gbn':
    return gbn.GoBackN(local_port, remote_port, msg_handler)

def make_packet(msg_type, seq_num, data):
    packet = b''
    # Type: 16 bit
    packet += struct.pack('!H', msg_type)
    # packet += msg_type.to_bytes(2, 'big')
    # Seq number: 16 bit
    packet += struct.pack('!H', seq_num)
    # packet += seq_num.to_bytes(2, 'big')
    # calculate checksum
    checksum = calc_checksum(msg_type, seq_num, data)
    # Checksum: 16 bit
    packet += struct.pack('!H', checksum)
    # packet += checksum.to_bytes(2, 'big')
    # Payload - None if it is an ACK
    if (data): 
        packet += data
    # print("Packet: ", packet)
    return packet

def calc_checksum(msg_type, seq_number, data):
    checksum = msg_type + seq_number
    if (data):
        data_len = len(data) - len(data) % 2
        for i in range(0, data_len, 2):
            val = int(data[i]) + 256 * int(data[i+1])
            checksum += val

        if (len(data) % 2 != 0): # Last byte if it's odd length
            checksum += data[-1]
    
    return checksum % pow(2, 16)

def is_corrupted(msg_type, seq_num, data, recv_checksum):
    return calc_checksum(msg_type, seq_num, data) != recv_checksum