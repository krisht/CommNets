Krishna Thiyagarajan
ECE 303: Communication Networks
February 19, 2018
Professor Shivam Mevawala
Port Scanner Miniproject Submission

The Pyhon scrip tattached is a port scanner which given a host and an optional range of ports will scan the host's ports and see if they're open or not, list the edefault serrvice on the port, the TTL size and the RCVBUF size (TCP window size) of each port. 


I used sockets to connect to a host's port and looked at the errno resulting for checking whether the port is openl or not. I used the socket.getsockopt in Python to get the ttl size nad the rcvbuf size. I limited the timeout to 0.5 seconds and used Python's Thread package (along with a Queue of jobs) to make the scanner run faster. Finally, the list of open ports are shown using the tabulate package. 

