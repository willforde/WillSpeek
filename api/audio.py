# Standard Library Imports
import pyaudio
import audioop
import Queue
import time

is_stopped = False

# Testing
try:
	import win32api
	import win32con
except:
	import threading
	lock = threading.Lock()

	def testing():
		from multiprocessing.connection import Listener

		address = ('localhost', 6000)     # family is deduced to be 'AF_INET'
		listener = Listener(address, authkey='dp23y4fm')

		while True:
			conn = listener.accept()
			if conn.recv_bytes() == "stop":
				print "Stopping Speeking"
				global is_stopped
				with lock: is_stopped = True

			conn.close()
		
		listener.close()

	t = threading.Thread(target=testing)
	t.daemon = True
	t.start()


# Setup Queue
audioChunks = Queue.Queue()
speachQueue = None
tts = None

# Setup Audio Player
p = pyaudio.PyAudio()
stream = p.open(format=pyaudio.paInt16, channels=2, rate=22050, output=True)

def stop_check():
	try: return win32api.GetAsyncKeyState(win32con.VK_F8)
	except:
		if is_stopped:
			global is_stopped
			is_stopped = False
			return True
		else:
			return False

def stop():
	# Clear the queue of audio chunks
	if audioChunks:
		with audioChunks.mutex:
			audioChunks.queue.clear()
	
	# Clear the queue of text left to process
	if speachQueue:
		with speachQueue.mutex:
			speachQueue.queue.clear()
	
	# Stop playback if stream is active
	if stream.is_active():
		stream.stop_stream()
		tries = 1
		while True:
			try: stream.start_stream()
			except:
				if tries <= 3:
					time.sleep(.1*tries)
					tries += 1
				else:
					global stream
					stream = p.open(format=pyaudio.paInt16, channels=2, rate=22050, output=True)
					print "Failed to Restart stream: Creating new Stream"
			else:
				break

def speeker():
	try:
		while True:
			try: data = audioChunks.get(True, 1)
			except Queue.Empty:
				if is_stopped:
					global is_stopped
					is_stopped = False
			else:	
				stream.write(audioop.tostereo(data, 2, 1, 1))
				audioChunks.task_done()
				if stop_check():
					stop()
	finally:
		print "closeing"
		stream.close()
		p.terminate()