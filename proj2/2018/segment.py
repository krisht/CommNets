import struct
from zlib import adler32

class TCPSegment:
	def __init__(self,seqnum=0,acknum=0,data=bytearray([])):
		self.seqnum = seqnum
		print('seqnum',self.seqnum)
		self.acknum = acknum
		print('acknum',self.acknum)
		self.data = data
		#print('Data',self.data)
		self.checksum = 0

	#Longitudinal Parity Check: Compute XOR of all bytes
	def make_checksum(self):
		self.checksum_ = adler32(str(self.seq)) % (2**16)
		self.cnum = struct.pack(">H", self.checksum_)	
		self.seq = bytearray(self.snum + self.anum + self.cnum) + bytearray(self.data)


	def pack(self):
		self.snum = struct.pack(">I", self.seqnum)
		self.anum = struct.pack(">I", self.acknum)
		self.cnum = struct.pack(">H", self.checksum)
		self.seq = bytearray(self.snum + self.anum + self.cnum) + bytearray(self.data)
		return self

	@staticmethod
	def unpack(seq):
		#print("unpack:", seq)
		seqnum = struct.unpack(">I", seq[0:4])[0]
		#print("seqnum", seq[0:4])
		acknum = struct.unpack(">I", seq[4:8])[0]
		#print("acknum", seq[4:8])
		checksum = struct.unpack(">H", seq[8:10])[0]
		#print("checksum", seq[8:10])
		data = seq[10:]	
		return seqnum, acknum, checksum, data
