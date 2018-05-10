# Written by S. Mevawala, modified by D. Gitzel

import logging

import channelsimulator
import utils
import sys
import socket

from segment import TCPSegment

class Receiver(object):

    def __init__(self, inbound_port=50005, outbound_port=50006, timeout=10, debug_level=logging.INFO):
        self.logger = utils.Logger(self.__class__.__name__, debug_level)

        self.inbound_port = inbound_port
        self.outbound_port = outbound_port
        self.simulator = channelsimulator.ChannelSimulator(inbound_port=inbound_port, outbound_port=outbound_port,
                                                           debug_level=debug_level)
        self.simulator.rcvr_setup(timeout)
        self.simulator.sndr_setup(timeout)

    def receive(self):
        raise NotImplementedError("The base API class has no implementation. Please override and add your own.")


class BogoReceiver(Receiver):
    ACK_DATA = bytes(123)

    def __init__(self):
        super(BogoReceiver, self).__init__()

    def receive(self):
        self.logger.info("Receiving on port: {} and replying with ACK on port: {}".format(self.inbound_port, self.outbound_port))
        while True:
            try:
                 data = self.simulator.u_receive()  # receive data
                 self.logger.info("Got data from socket: {}".format(
                     data.decode('ascii')))  # note that ASCII will only decode bytes in the range 0-127
                 sys.stdout.write(data)
                 self.simulator.u_send(BogoReceiver.ACK_DATA)  # send ACK
            except socket.timeout:
                sys.exit()

class BroReceiver(BogoReceiver):

    def __init__(self):
        super(BroReceiver, self).__init__()

    def receive(self):
        self.logger.info("Receiving on port: {} and replying with ACK on port: {}".format(self.inbound_port, self.outbound_port))
        self.seqnum = 0
        self.timeout_interval = 0.01 #Same as sender timeout
        self.simulator.rcvr_socket.settimeout(self.timeout_interval)
        #self.simulator.rcvr_socket.settimeout(0.5) #500 ms suggested in book
        #Congestion control
        self.duplicate_limit = 5 
        self.duplicate_count = 0
        self.prev_seg = None #For duplicate ACKs
        self.prev_seq = 0
        self.prev_num_bytes = 0
        while True:
            while True:
                try:
                    rcv_seg_ = self.simulator.u_receive()  # receive data
                    rcv_seg = TCPSegment.unpack(rcv_seg_)
                    if utils.check_checksum(rcv_seg_):
                        print('Received valid data')
                        self.duplicate_count = 0
                        break
                except socket.timeout:
                    #print('Timeout')
                    if self.prev_seg:
                        if self.duplicate_count < self.duplicate_limit:
                            print('Send duplicate ack',self.duplicate_count)
                        self.simulator.u_send(self.prev_seg)
                        self.duplicate_count+=1
            #print('Rcv_seg',rcv_seg)
            data = rcv_seg[3]
            num_bytes = len(data)
            if (self.prev_seq + self.prev_num_bytes) == rcv_seg[0]:
                print('Received segment in-order')
                #Print
                self.logger.info("Got data from socket: {}".format(data.decode('ascii')))  # note that ASCII will only decode bytes in the range 0-127
                with open("out.txt", "a") as file: 
                    file.write(data.decode('ascii'))
                #Send ACK
                self.acknum = rcv_seg[0]+num_bytes
                print('Send ACK',self.acknum)
                temp = TCPSegment(self.seqnum,self.acknum) #data empty
                temp.pack()
                temp.make_checksum()
                self.prev_seg = temp.seq
                self.simulator.u_send(self.prev_seg)
                #Update prev_seq
                self.prev_seq = rcv_seg[0]
                #print('Prev Seq',self.prev_seq)
                self.prev_num_bytes = num_bytes
                #print('Prev Num Bytes',self.prev_num_bytes)
            else:
                print('Received segment out-of-order')
                #Discard and send duplicate ACK
                self.acknum = self.prev_seq+self.prev_num_bytes
                print('Send Duplicate ACK',self.acknum)
                temp = TCPSegment(self.seqnum,self.acknum) #data empty
                temp.pack()
                temp.make_checksum()
                self.prev_seg = temp.seq
                self.simulator.u_send(self.prev_seg)              



if __name__ == "__main__":
    # test out BogoReceiver
    rcvr = BroReceiver()
    rcvr.receive()