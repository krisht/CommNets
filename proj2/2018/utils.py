import datetime
import logging
import sys
from zlib import adler32
from segment import TCPSegment

def check_checksum(seg):
    seqnum, acknum, checksum, data = TCPSegment.unpack(seg)

    actual_chksum = adler32(str(TCPSegment(seqnum, acknum, data).pack().seq)) % (2**16)

    return True if checksum == actual_chksum else False



class Logger(object):

    def __init__(self, name, debug_level):
        now = datetime.datetime.now()
        #logging.basicConfig(filename='{}_{}.log'.format(name, datetime.datetime.strftime(now, "%Y_%m_%dT%H%M%S")), level=debug_level)
        logging.basicConfig(stream=sys.stdout, level=debug_level)

    @staticmethod
    def info(message):
        logging.info(message)

    @staticmethod
    def debug(message):
        logging.debug(message)
