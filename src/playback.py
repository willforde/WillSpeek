# Standard Library Imports
import queue

# Third Party Imports
import pyaudio

# Audio Frame Queue
frames = queue.Queue()


def callback(in_data, frame_count, time_info, status):
    try:
        return frames.get(), pyaudio.paContinue
    finally:
        frames.task_done()


def listen():
    # Setup Audio Player
    player = pyaudio.PyAudio()
    stream = player.open(rate=44100, channels=2, format=pyaudio.paInt16, output=True, stream_callback=callback)
    stream.start_stream()
    return player, stream
