import udt
import util
import config

# Go-Back-N reliable transport protocol.
class GoBackN:
	# "msg_handler" is used to deliver messages to application layer
	# when it's ready.
	def __init__(self, local_port, remote_port, msg_handler):
		self.network_layer = udt.NetworkLayer(local_port, remote_port, self)
		self.msg_handler = msg_handler
		self.send_window = []
		self.window_start = 1 # start index of the send window
		self.next_seq_number = 0
		self.timer = None

	# "send" is called by application. Return true on success, false
	# otherwise.
	def send(self, msg):
		# TODO: impl protocol to send packet from application layer.
		# Assumption: sender only sends data via transport layer while receiver only sends ack via network layer
		# Call self.network_layer.send() to send to network layer.
		packet = util.make_packet(config.MSG_TYPE_DATA, self.next_seq_number, msg)
		self.send_window[self.next_seq_number] = packet
		self.network_layer.send(packet)
		if (self.window_start == self.next_seq_number):
			self.timer = threading.Timer(config.TIMEOUT_MSEC/1000, self.resend_all)
		self.next_seq_number += 1

		# stop accepting input if window is full
		return self.window_start < config.WINDOW_SIZE

	# Send all unacknowledge packets and restart timer
	def resend_all(self):
		self.timer = threading.Timer(config.TIMEOUT_MSEC/1000, self.resend_packet, packet)
		for i in range(self.window_start, self.next_seq_number):
			self.network_layer.send(packet)
		

	# "handler" to be called by network layer when packet is ready.
	def handle_arrival_msg(self):
		# TODO: impl protocol to handle arrived packet from network layer.
		# Assumption: receiver only receives data while sender only receives ack
		# Call self.msg_handler() to deliver to application layer.
		msg = self.network_layer.recv()

		# validate checksum
		msg_type = struct.unpack('<H', msg[0:2])[0] # first 2 bytes
		seq_num = struct.unpack('<H', msg[2:4])[0] # next 2 bytes
		recv_checksum = struct.unpack('<H', msg[4:6])[0] # next 2 bytes

		if (msg_type == config.MSG_TYPE_ACK): # if this is the sender
			calculated_checksum = util.calc_checksum(msg_type, seq_num, None)
			if (recv_checksum == calculated_checksum):
				if (self.window_start == seq_num + 1):
					self.timer.cancel()
				else:
					self.timer = threading.Timer(config.TIMEOUT_MSEC/1000, self.resend_all)
			else:
				pass

		else: # this is the receiver
			pass


		

	# Cleanup resources.
	def shutdown(self):
		# TODO: cleanup anything else you may have when implementing this
		# class.
		self.network_layer.shutdown()
