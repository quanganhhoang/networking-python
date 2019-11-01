import udt
import threading
import config
import struct
import util

# Stop-And-Wait reliable transport protocol.
class StopAndWait:
	# "msg_handler" is used to deliver messages to application layer
	# when it's ready.
	
	def __init__(self, local_port, remote_port, msg_handler):
		self.network_layer = udt.NetworkLayer(local_port, remote_port, self)
		self.msg_handler = msg_handler
		self.seq_number = 0
		self.timer = None
		self.awaiting_mes = 0 # 0 if awaiting new message and 1 if awaiting an ACK
		self.file_id = 1

	# "send" is called by application. Return true on success, false
	# otherwise.
	def send(self, msg):
		# TODO: impl protocol to send packet from application layer.
		# Assumption: sender only sends data via transport layer while receiver only sends ack via network layer
		# Call self.network_layer.send() to send to network layer.
		packet = util.make_packet(config.MSG_TYPE_DATA, self.seq_number, msg)
		self.awaiting_mes = 1
		self.timer = threading.Timer(config.TIMEOUT_MSEC/1000, self.resend_packet, [packet]) # fire the timer
		self.timer.start()
		self.network_layer.send(packet)

		while (self.awaiting_mes == 1):
			pass

		return True
		
	# function to resend a packet and restart the timer
	def resend_packet(self, packet):
		if (self.awaiting_mes == 1):
			self.timer = threading.Timer(config.TIMEOUT_MSEC/1000, self.resend_packet, [packet])
			self.timer.start()
			self.network_layer.send(packet)

	# "handler" to be called by network layer when packet is ready.
	def handle_arrival_msg(self):
		# Assumption: receiver only receives data while sender only receives ack
		msg = self.network_layer.recv()
		# validate checksum
		msg_type = struct.unpack('!H', msg[:2])[0] # first 2 bytes
		# msg_type = int.from_bytes(msg[0:2], 'big')
		seq_num = struct.unpack('!H', msg[2:4])[0] # next 2 bytes
		# seq_num = int.from_bytes(msg[2:4], 'big')
		recv_checksum = struct.unpack('!H', msg[4:6])[0] # next 2 bytes
		# recv_checksum = int.from_bytes(msg[4:6], 'big')
		data = msg[6:]
		
		if (util.is_corrupted(msg_type, seq_num, data, recv_checksum)):
			if (data): # receiver sends ACK - sender does nothing in case of packet corruption
				self.network_layer.send(util.make_packet(config.MSG_TYPE_ACK, self.seq_number ^ 1, None))
			return

		if (msg_type == config.MSG_TYPE_ACK): # if this is the sender
			print('Sender - MSG_TYPE: ', msg_type)
			print('Sender - SEQ_NUM: ', seq_num)
			if (seq_num != self.seq_number):
				return
			else:
				if (self.timer and self.timer.is_alive()):
					self.timer.cancel() # ACK received, cancelling timer
				
				print('Sender - Received ACK for seq #', seq_num)
				self.seq_number ^= 1
				self.awaiting_mes = 0
				print('Sender - Sent file #', self.file_id)
				self.file_id += 1
		elif (msg_type == config.MSG_TYPE_DATA): # else this is the receiver
			print('Receiver - MSG_TYPE: ', msg_type)
			print('Receiver - SEQ_NUM: ', seq_num)

			if (seq_num == self.seq_number):
				print("Receiver - Writing to file...#", self.file_id)
				self.file_id += 1
				self.msg_handler(data) # write out received data
				# if received the correct message, send back an ACK(rcvpkt, seq_num)
				packet = util.make_packet(config.MSG_TYPE_ACK, seq_num, None)
				# print('Receiver - Sending ACK for seq #', seq_num)
				self.network_layer.send(packet) # sending ACK
				self.seq_number ^= 1 # toggle sequence number
			else:
				packet = util.make_packet(config.MSG_TYPE_ACK, self.seq_number ^ 1, None) # send ACK of previous sequence number
				# print('Receiver - Re-sending ACK for seq #', seq_num)
				self.network_layer.send(packet)


	# Cleanup resources.
	def shutdown(self):
		# TODO: cleanup anything else you may have when implementing this class
		if (self.timer):
			 self.timer.cancel()

		self.network_layer.shutdown()

	


