#!/usr/bin/env python2
from multiprocessing.connection import Client

address = ('localhost', 6000)
conn = Client(address, authkey='dp23y4fm')
conn.send_bytes('stop')
conn.close()
