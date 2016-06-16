# Standard Library Imports
import threading
import weakref
import logging
import socket
import Queue
import sys
import os

# Package imports
from api.sapiLocal import TTSClient
from api import logger, CHUNK

# Parameters
HEADERSIZE = 50
BIND_PORT = 9999
BIND_IP = "0.0.0.0"

# Setup Queues
commandQueue = Queue.Queue()
clientData = {}

class SocketServer(threading.Thread):
	def __init__(self, ip, port):
		threading.Thread.__init__(self)
		self.tcpsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.tcpsock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		self.tcpsock.bind((ip, port))
		self.tcpsock.listen(5)
		
		# Log to user
		logger.info("Listening for incoming connections on port: %s", port)
	
	def run(self):
		try: self.loop_accept()
		finally: self.tcpsock.close()
	
	def loop_accept(self):
		while True:
			# Wait for connection from client
			(clientsock, (ip, port)) = self.tcpsock.accept()
			newthread = ClientThread(clientsock, ip, port)
			newthread.start()


class ClientThread(threading.Thread):
	def __init__(self, conn, ip, port):
		logger.info("Got connection from %s on port %s", ip, port)
		threading.Thread.__init__(self)
		self._conn = conn
		self._port = port
		self._ip = ip
		
		# Create queue for client
		self.queue = Queue.Queue()
		clientData[port] = {"queue":self.queue}
	
	def run(self):
		try:
			self.check_client()
		finally:
			logger.info("Connection from %s on port %s has closed", self._ip, self._port)
			self._conn.close()
			self.queue = None
			del clientData[self._port]
	
	def check_client(self):
		# Loop until connection is closed
		while True:
			# Wait for data header from client
			try: command, value = self.recv_header()
			except: break
			if not command:
				continue
			
			# Fetch the text that will be sent after this header and speaks the text
			if command == "speek":
				text = "".join([self._conn.recv(segment) for segment in self.cal_len(int(value))])
				commandQueue.put((self._port, (command, text)))
				
				# Wait for audioObj, then send back to client
				audioObj = self.queue.get()
				self.send_audio(audioObj)
				self.queue.task_done()
			
			# Sets the rate of the speach or the volume
			elif command == "set_rate" or command == "set_volume":
				commandQueue.put((self._port, (command, int(value))))
			
			# Sets the voice to use
			elif command == "set_voice":
				voiceID = self._conn.recv(int(value))
				commandQueue.put((self._port, (command, voiceID)))
			
			elif command == "get_voice" or command == "get_voices":
				commandQueue.put((self._port, (command, None)))
				
				# Wait for available voices to be returned
				voices = self.queue.get()
				self.send_header("voicedata", len(voices))
				self._conn.send(voices)
				self.queue.task_done()
			
			elif command == "get_rate" or command == "get_volume":
				commandQueue.put((self._port, (command, None)))
				
				property = self.queue.get()
				self.send_header("property", property)
				self.queue.task_done()
	
	def send_audio(self, audioObj):
		try:
			# Fetch the length of the audioObj
			audioObj.seek(0, os.SEEK_END)
			length = audioObj.tell()
			audioObj.seek(0, os.SEEK_SET)
			
			# Send header reporting body length
			self.send_header("audio", length)
			
			data = audioObj.read(CHUNK)
			while data:
				self._conn.send(data)
				data = audioObj.read(CHUNK)
			
			audioObj.close()
		except:
			logger.info("problem sending audio to client %s on port %s", self._ip, self._port)
	
	def send_header(self, command, value):
		commandStr = ("[%s:%s]" % (command, value)).ljust(HEADERSIZE)
		self._conn.send(commandStr)
	
	def recv_header(self):
		# Wait for data header from client
		try: header = self._conn.recv(HEADERSIZE)
		except: raise
		
		# If no valid header is reversed then break
		if not header: raise
		
		# Split header into command / value
		if header.startswith("[") and ":" in header:
			return header.strip()[1:-1].lower().split(":", 1)
		else:
			logger.info("invalid header received: %s", header)
			return ("", "")
	
	@staticmethod
	def cal_len(length):
		new = [CHUNK for i in range(length/CHUNK)]
		if sum(new) < length: new.append(length % CHUNK)
		return new


# Start the socket server
socThread = SocketServer(BIND_IP, BIND_PORT)
socThread.start()

while True:
	# Wait till data is avilable
	(portId, (command, value)) = commandQueue.get()
	
	# Fetch tts engine for requesting client
	client = clientData[portId]
	if not "tts_engine" in client: client["tts_engine"] = TTSClient(server_mode=True)
	
	# Speak text
	if command == "speek":
		client["tts_engine"].speek(value)
		audioObj = client["tts_engine"]._audio_frames()
		client["queue"].put(audioObj)
	
	# Set Rate
	elif command == "set_rate":
		client["tts_engine"].rate = value
	
	# Get Rate
	elif command == "get_rate":
		client["queue"].put(client["tts_engine"].rate)
	
	# Set volume
	elif command == "set_volume":
		client["tts_engine"].volume = value
	
	# Get volume
	elif command == "get_volume":
		client["queue"].put(client["tts_engine"].volume)
	
	# Set voice
	elif command == "set_voice":
		for voice in client["tts_engine"].get_voices():
			if voice.id == value:
				client["tts_engine"].voice = voice
	
	# Get voice
	elif command == "get_voice":
		voice = client["tts_engine"].voice
		data = "%s=%s" % (voice.id, voice.name)
		client["queue"].put(data)
	
	# Get voice
	elif command == "get_voices":
		voices = ["%s=%s" % (voice.id, voice.name) for voice in client["tts_engine"].get_voices()]
		client["queue"].put("&".join(voices))
	
	# Single that that the task has completed
	commandQueue.task_done()
