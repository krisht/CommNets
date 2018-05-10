# Written by S. Mevawala, modified by D. Gitzel

import argparse
import logging
import socket

import channelsimulator
import utils
import time
import math
import sys

from segment import TCPSegment


class Sender(object):

	def __init__(self, inbound_port=50006, outbound_port=50005, timeout=10, debug_level=logging.INFO):
		self.logger = utils.Logger(self.__class__.__name__, debug_level)

		self.inbound_port = inbound_port
		self.outbound_port = outbound_port
		self.simulator = channelsimulator.ChannelSimulator(inbound_port=inbound_port, outbound_port=outbound_port,
														   debug_level=debug_level)
		self.simulator.sndr_setup(timeout)
		self.simulator.rcvr_setup(timeout)

	def send(self, data):
		raise NotImplementedError("The base API class has no implementation. Please override and add your own.")


class BogoSender(Sender):

	def __init__(self):
		super(BogoSender, self).__init__()

	def send(self, data):
		self.logger.info("Sending on port: {} and waiting for ACK on port: {}".format(self.outbound_port, self.inbound_port))
		while True:
			try:
				self.simulator.u_send(data)  # send data
				ack = self.simulator.u_receive()  # receive ACK
				self.logger.info("Got ACK from socket: {}".format(
					ack.decode('ascii')))  # note that ASCII will only decode bytes in the range 0-127
				break
			except socket.timeout:
				pass


class BroSender(BogoSender):
	def __init__(self):
		super(BroSender, self).__init__()

	def send(self, data, data_len):
		self.data = data
		self.data_len = data_len

		self.mss = 1000 #Slightly less than 1024
		#self.num_segments = int(math.ceil(self.data_len/self.mss))
		self.num_sent = 0

		self.logger.info("Sending on port: {} and waiting for ACK on port: {}".format(self.outbound_port, self.inbound_port))

		self.seqnum = 0
		self.acknum = 0

		self.sendbase = 0
		self.congestion_window_size = 5 #Increase for more segments sent at a time, Decrease for TCP Fairness

		self.is_congested = False #TCP Fairness
		self.duplicate_count = 0
		self.timeout_interval = 0.01
		self.simulator.sndr_socket.settimeout(self.timeout_interval)

		while True:
			#For seqnum
			self.seqnum = self.sendbase
			#Find sendbase value when all segments in window have been successfully received
			self.send_success = self.sendbase + self.mss*self.congestion_window_size
			print('Send Success',self.send_success)
			#Tune sliding window (TCP Fairness)
			if self.is_congested:
				if self.congestion_window_size > 1:
					#Multiplicative decrease
					self.congestion_window_size /= 2
			else:
				#Additive increase
				self.congestion_window_size += 1
			print('Congestion Window Size',self.congestion_window_size)
			self.duplicate_count = 0
			#Send data
			for i in range(self.congestion_window_size):
				if(self.seqnum >= data_len):
					print('End window early')
					break
				elif(self.seqnum+self.mss > data_len):
					print('Segment smaller than MSS')
					data_ = self.data[self.seqnum:]
				else:
					print('Segment')
					data_  = self.data[self.seqnum:self.seqnum+self.mss]
				seg = TCPSegment(self.seqnum,self.acknum,data_)
				seg.pack()
				seg.make_checksum()
				#print(utils.check_checksum(seg.seq))
				self.simulator.u_send(seg.seq)
				print('Seg sent',self.seqnum)
				self.num_sent += 1
				self.seqnum+=self.mss
			#Handle ACKs
			while True:
				#Timeouts
				try:
					rcv_seg_ = self.simulator.u_receive()
					rcv_seg = TCPSegment.unpack(rcv_seg_)
					if utils.check_checksum(rcv_seg_):
						print('Check succeeded')
						if(rcv_seg[1] > self.sendbase):
							print('Received ACK')
							#Cumalitive ACK - Update sendbase
							self.sendbase = rcv_seg[1]
							print('Sendbase',self.sendbase)
							#Reset duplicate count
							self.duplicate_count = 0
							if self.sendbase >= data_len:
								print('Last ACK recieved, return')
								return
							if self.sendbase == self.send_success:
								print('All segments in window have been successfully ACKed')
								self.is_congested = False
								break
						else:
							self.duplicate_count+=1
							print('Duplicate ACK',self.duplicate_count)
							#Fast Retransmit
							if self.duplicate_count >= 3:
								print('Fast Retransmit')
								self.is_congested = True
								break
					else:
						print('Check failed')
						self.is_congested = True
				except socket.timeout:
					print('Timeout')
					self.is_congested = True
					break

def data_to_bin(data_file):
	data = open(data_file, 'r').read()
	bin_rep = ''.join(format(ord(x), '08b') for x in data)
	return len(data), bin_rep


if __name__ == "__main__":
	open("out.txt", 'w')
	data = bytearray(sys.stdin.read())
	num_bytes = len(data)
	#print('Num_bytes',num_bytes)
	data_bin = data
	#num_bytes, data_bin = data_to_bin(vars(parser.parse_args())['data'])
	sndr = BroSender()
	start_time = time.time()
	sndr.send(data_bin,num_bytes)
	print("Throughput: %.3f bytes / sec"%(num_bytes/(time.time() - start_time)))

