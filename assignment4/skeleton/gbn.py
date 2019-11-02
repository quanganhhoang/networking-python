import udt
import util
import config
import threading
import struct

# Go-Back-N reliable transport protocol.
class GoBackN:
	# "msg_handler" is used to deliver messages to application layer
	# when it's ready.
	def __init__(self, local_port, remote_port, msg_handler):
		self.network_layer = udt.NetworkLayer(local_port, remote_port, self) # [Sender/Receiver]
		self.msg_handler = msg_handler # [Sender/Receiver]
		self.send_window = [None] * config.WINDOW_SIZE * 2 # [Sender]
		self.window_start = 1 # start index of the send window [Sender/Receiver]
		self.next_seq_number = 1 # [Sender/Receiver]
		self.timer = None # [Sender]
		self.file_id = 0 # [Sender/Receiver]

	# "send" is called by application. Return true on success, false
	# otherwise.
	def send(self, msg):
		# TODO: impl protocol to send packet from application layer.
		# Assumption: sender only sends data via transport layer while receiver only sends ack via network layer
		# Call self.network_layer.send() to send to network layer.
		
		if (self.next_seq_number < self.window_start + config.WINDOW_SIZE):
			packet = util.make_packet(config.MSG_TYPE_DATA, self.next_seq_number, msg)
			self.send_window[self.next_seq_number % (config.WINDOW_SIZE * 2)] = packet
			if (self.window_start == self.next_seq_number):
				self.timer = threading.Timer(config.TIMEOUT_MSEC/1000, self.resend_all)
				self.timer.start()
			print("Sender - Sending packet #", self.file_id)
			self.network_layer.send(packet)
			self.next_seq_number += 1
			# self.next_seq_number = self.next_seq_number % (2 * config.WINDOW_SIZE)
			self.file_id += 1

			return True
		else:
			return False

	# Send all unacknowledge packets and restart timer
	def resend_all(self):
		print("Sender - Resending packets from {0} to {1}".format(self.window_start, self.next_seq_number))
		
		self.timer = threading.Timer(config.TIMEOUT_MSEC/1000, self.resend_all)
		self.timer.start()
		for i in range(self.window_start, self.next_seq_number):
			i = i % (config.WINDOW_SIZE * 2)
			self.network_layer.send(self.send_window[i])
			

	# "handler" to be called by network layer when packet is ready.
	def handle_arrival_msg(self):
		# TODO: impl protocol to handle arrived packet from network layer.
		# Assumption: receiver only receives data while sender only receives ack
		# Call self.msg_handler() to deliver to application layer.
		msg = self.network_layer.recv()

		# validate checksum
		msg_type = struct.unpack('!H', msg[:2])[0] # first 2 bytes
		seq_num = struct.unpack('!H', msg[2:4])[0] # next 2 bytes
		recv_checksum = struct.unpack('!H', msg[4:6])[0] # next 2 bytes
		data = msg[6:]

		if (util.is_corrupted(msg_type, seq_num, data, recv_checksum)):
			if (data): # receiver sends ACK - sender does nothing in case of packet corruption
				self.network_layer.send(util.make_packet(config.MSG_TYPE_ACK, self.next_seq_number - 1, None))
			return

		if (msg_type == config.MSG_TYPE_ACK): # if this is the sender
			# print('Sender - MSG_TYPE: ', msg_type)
			# print('Sender - SEQ_NUM: ', seq_num)
			if (self.window_start <= seq_num <= self.next_seq_number): # if receiving ACK for any of the packet in send_window
				print("Sender - Receiving ACK #", seq_num)
				self.window_start = seq_num + 1 # move window_start index
				if (self.window_start == self.next_seq_number):
					self.timer.cancel()
					self.timer.join()
				else:
					self.timer = threading.Timer(config.TIMEOUT_MSEC/1000, self.resend_all)
					self.timer.start()
				# self.window_start = self.window_start % (2 * config.WINDOW_SIZE)
		elif (msg_type == config.MSG_TYPE_DATA): # this is the receiver
			# print('Receiver - MSG_TYPE: ', msg_type)
			# print('Receiver - SEQ_NUM: ', seq_num)
			if (seq_num == self.next_seq_number):
				print("Receiver - Writing file #", self.file_id)
				self.file_id += 1
				self.msg_handler(data)
				packet = util.make_packet(config.MSG_TYPE_ACK, seq_num, None)
				self.network_layer.send(packet)
				self.next_seq_number += 1
			else:
				# resend the last ACK packet
				self.network_layer.send(util.make_packet(config.MSG_TYPE_ACK, self.next_seq_number - 1, None))

	# Cleanup resources.
	def shutdown(self):
		# TODO: cleanup anything else you may have when implementing this
		# class.
		if (self.timer):
			self.timer.cancel() 
			self.timer.join()
		self.network_layer.shutdown()
