# Standard Library Imports
import threading
import urlparse
import socket

# Package Imports
from .voice import Voice
from .audio import speeker, audioChunks
from . import logger, CHUNK

# Parameters
HEADERSIZE = 50
BIND_PORT = 9999
BIND_IP = "192.168.1.61"

class TTSClient(object):
	def __init__(self):
		# Start the speeker thread and start listening for audioChunks
		t = threading.Thread(target=speeker)
		t.daemon = True
		t.start()
		
		# Connect to TTS server
		self.tcpsock = socket.socket()
		self.tcpsock.connect((BIND_IP, BIND_PORT))
	
	def _send_header(self, command, value):
		commandStr = ("[%s:%s]" % (command, value)).ljust(HEADERSIZE)
		self.tcpsock.send(commandStr)
	
	def _recv_header(self):
		# Wait for data header from client
		try: header = self.tcpsock.recv(HEADERSIZE)
		except: raise
		
		# If no valid header is reversed then break
		if not header: raise
		
		# Split header into command / value
		if header.startswith("[") and ":" in header:
			return header.strip()[1:-1].lower().split(":", 1)
		else:
			logger.info("invalid header received: %s", header)
			return ("", "")
	
	def _get_voice_data(self):
		command, value = self._recv_header()
		if not command == "voicedata":
			print command, value
			return {}
		else: length = int(value)
		
		voicesData = []
		count = 0
		while count < length:
			left = length - count
			data = self.tcpsock.recv(CHUNK if left > CHUNK else left)
			count += len(data)
			voicesData.append(data)
		
		# Recombine voices into dict
		return [Voice(None, voiceID, name[0]) for voiceID, name in urlparse.parse_qs("".join(voicesData)).iteritems()]
	
	def _audio_frames(self):
		command, value = self._recv_header()
		if not command == "audio": return None
		else: length = int(value)
		
		count = 0
		while count < length:
			left = length - count
			data = self.tcpsock.recv(CHUNK if left > CHUNK else left)
			count += len(data)
			audioChunks.put(data)
	
	def speek(self, testToSpeech):
		""" Send text to tts engine and speak """
		self._send_header("speek", len(testToSpeech))
		self.tcpsock.send(testToSpeech)
		self._audio_frames()
	
	def get_voices(self):
		""" Return list of avalable voices as a Voice object """
		self._send_header("get_voices", "null")
		return self._get_voice_data()
	
	@property
	def voice(self):
		""" Return the current selected voice as a Voice object """
		self._send_header("get_voice", "null")
		return self._get_voice_data()[0]
	
	@voice.setter
	def voice(self, voice):
		"""
		Change voice to selected voice Token
		
		value : Voice obj --- The voice of witch to change too
		"""
		self._send_header("set_voice", len(voice.id))
		self.tcpsock.send(voice.id)
	
	@property
	def rate(self):
		""" Return the current speech rate """ 
		self._send_header("get_rate", "null")
		command, value = self._recv_header()
		if command == "property": return int(value)
	
	@rate.setter
	def rate(self, value):
		"""
		Change the speach rate of the voice
		
		value : integer --- Rate to set the voice to
		
		Value must be between -10 to +10
		"""
		value = int(value)
		if value < -10 or value > 10: raise ValueError("invalid rate %s" % value)
		else: self._send_header("set_rate", value)
	
	@property
	def volume(self):
		""" Return the current volume level """
		self._send_header("get_volume", "null")
		command, value = self._recv_header()
		if command == "property": return int(value)
	
	@volume.setter
	def volume(self, value):
		"""
		Chagne the volume of the voice
		
		value : int --- level of the volume to change to
		"""
		if value < 0 or value >100: raise ValueError("invalid volume %s" % value)
		else: self._send_header("set_volume", value)
