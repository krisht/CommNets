import sys

try:
	assert sys.version_info >= (3,)
except AssertionError:
	sys.stdout.write('Run with python3...\n')
	sys.exit(-1)

import argparse
import errno
import socket
from queue import Queue
from threading import Thread
from tabulate import tabulate

errno.errorcode[errno.ECONNREFUSED] = 'No Response'
errno.errorcode[0] = 'Open'
errno.errorcode[errno.EAGAIN] = 'Closed'
errno.errorcode[errno.EHOSTUNREACH] = 'Host Unreachable'


class ScanThread(Thread):
	def __init__(self):
		Thread.__init__(self)

	def run(self):
		while not q.empty():
			h, p = q.get()
			self.__scan__(h, p)

	@staticmethod
	def __scan__(host, port):
		try:
			s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
			s.settimeout(1.0)
			res = s.connect_ex((host, port))
			try:
				serv = ' '.join((socket.getservbyport(port)).split())
			except OSError:
				serv = ""
			table_data.append([host, port, errno.errorcode[res], serv])
			if res == errno.EAGAIN:
				return
			s.close()
		# except KeyboardInterrupt:
		# 	print("Error: Ctrl + C encountered. Exiting...")
		# 	sys.exit()
		except socket.gaierror:
			print("Error: Host %s not found..." % host)
			sys.exit()
		except socket.error:
			print("Error: Could not connect to server...")
			sys.exit()


if __name__ == '__main__':
	parser = argparse.ArgumentParser(description='Scans ports of given hosts from starting port to ending port excluding the ending port.')
	parser.add_argument("host", help="host to scan")
	parser.add_argument('-p', '--ports', help='starting port (inclusive)', default='0:1024')
	args = vars(parser.parse_args())
	host = args['host']
	start, end = tuple(args['ports'].split(':'))
	start = int(start)
	end = int(end)

	if end < start:
		print("Error: End port is lower than start port")
		sys.exit()
	
	ports = list(range(int(start), int(end)+1))

	table_data = []

	q = Queue()
	for pp in ports:
		q.put((host, pp))

	n_threads = 30
	threads = []

	for _ in range(n_threads):
		temp = ScanThread()
		temp.start()
		threads.append(temp)

	try:
		for t in threads:
			t.join()
	except KeyboardInterrupt:
		print("Error: Ctrl + C encountered. Exiting...")
		sys.exit()

	print(tabulate(table_data, headers=['Host', 'Port', 'Status', 'Protocol'], tablefmt='orgtbl'))
