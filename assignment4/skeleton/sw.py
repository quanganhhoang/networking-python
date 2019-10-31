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
		self.await_mes = 0 # 0 for awaiting a message and 1 for awaiting an ack

	# "send" is called by application. Return true on success, false
	# otherwise.
	def send(self, msg):
		# TODO: impl protocol to send packet from application layer.
		# Assumption: sender only sends data via transport layer while receiver only sends ack via network layer
		# Call self.network_layer.send() to send to network layer.
		packet = util.make_packet(config.MSG_TYPE_DATA, self.seq_number, msg)
		
		self.await_mes = 1 # awaiting an ACK
		self.network_layer.send(packet)
		self.timer = threading.Timer(config.TIMEOUT_MSEC/1000, self.resend_packet, [packet]) # fire the timer
		self.timer.start()

		return self.await_mes == 0
		
	# function to resend a packet and restart the timer
	def resend_packet(self, packet):
		if (self.await_mes == 1):
			self.network_layer.send(packet)
			self.timer = threading.Timer(config.TIMEOUT_MSEC/1000, self.resend_packet, [packet])
			self.timer.start()

	# "handler" to be called by network layer when packet is ready.
	def handle_arrival_msg(self):
		# Assumption: receiver only receives data while sender only receives ack
		msg = self.network_layer.recv()
		# validate checksum
		msg_type = struct.unpack('<H', msg[0:2])[0] # first 2 bytes
		seq_num = struct.unpack('<H', msg[2:4])[0] # next 2 bytes
		recv_checksum = struct.unpack('<H', msg[4:6])[0] # next 2 bytes

		if (msg_type == config.MSG_TYPE_ACK): # if this is the sender
			calculated_checksum = util.calc_checksum(msg_type, seq_num, None)
			if (recv_checksum != calculated_checksum or seq_num != self.seq_number):
				pass
			else:
				if (self.timer.is_alive()):
					self.timer.cancel() # ACK received, cancelling timer
				
				self.seq_number ^= 1
				self.await_mes = 0
		else: # else this is the receiver
			data = msg[6:] # rest of message
			calculated_checksum = util.calc_checksum(msg_type, seq_num, data)
			if (calculated_checksum == recv_checksum and seq_num == self.seq_number):
				# if received the correct message, send back an ACK(rcvpkt, seq_num)
				packet = util.make_packet(config.MSG_TYPE_ACK, seq_num, None)
				self.network_layer.send(packet) # sending ACK
				self.seq_number ^= 1 # toggle sequence number
				self.msg_handler(data) # write out received data
			else:
				packet = util.make_packet(config.MSG_TYPE_ACK, seq_num, None) # send ACK of previous sequence number
				self.network_layer.send(packet)

		# TODO: impl protocol to handle arrived packet from network layer.
		# call self.msg_handler() to deliver to application layer.


	# Cleanup resources.
	def shutdown(self):
		# TODO: cleanup anything else you may have when implementing this class
		if (self.timer):
			 self.timer.cancel()
		self.network_layer.shutdown()

	


