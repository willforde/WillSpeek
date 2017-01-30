# Standard Library Imports
import cStringIO
import threading

# Package Imports
from .voice import Voice
from . import logger, CHUNK

# Dependency Packages
try:
    from comtypes.client import CreateObject
except ImportError:
    raise ImportError("Missing required dependency: comtypes (https://pypi.python.org/pypi/comtypes)")


class TTSClient(object):
    """ Driver module to control microsoft SAPI TTS Engine """

    def __init__(self, server_mode=False):
        # Check for Server Mode
        self.server_mode = server_mode
        if server_mode is False:
            from .audio import speeker, audioChunks
            self.audioChunks = audioChunks

            # Start the speeker thread and start listening for audioChunks
            t = threading.Thread(target=speeker)
            t.daemon = True
            t.start()

        self._engine = CreateObject("SAPI.SPVoice")
        self._stream = CreateObject("SAPI.SpMemoryStream")
        self._engine.AudioOutputStream = self._stream

    def _audio_frames(self):
        """ Return the spoken text as an audio stream """
        try:
            return cStringIO.StringIO(bytearray(self._stream.GetData()))
        finally:
            del self._stream
            self._stream = CreateObject("SAPI.SpMemoryStream")
            self._engine.AudioOutputStream = self._stream

    def _play_frames(self):
        audioObj = self._audio_frames()
        while True:
            frames = audioObj.read(CHUNK)
            if not frames:
                break
            else:
                self.audioChunks.put(frames)

    def speek(self, text):
        """ Send text to tts engine and speak """
        self._engine.Speak(text)
        if self.server_mode is False: self._play_frames()

    def stop(self):
        self._engine.Speak("", 3)

    def get_voices(self):
        """ Return list of avalable voices as a Voice object """
        return [Voice(attr, attr.Id, attr.GetDescription()) for attr in self._engine.GetVoices()]

    @property
    def voice(self):
        """ Return the current selected voice as a Voice object """
        _voice = self._engine.Voice
        return Voice(_voice, _voice.Id, _voice.GetDescription())

    @voice.setter
    def voice(self, value):
        """
        Change voice to selected voice Token

        value : Voice obj --- The voice of witch to change too
        """
        self._engine.Voice = value._token

    @property
    def rate(self):
        """ Return the current speech rate """
        return self._engine.Rate

    @rate.setter
    def rate(self, value):
        """
        Change the speach rate of the voice

        value : integer --- Rate to set the voice to

        Value must be between -10 to +10
        """
        if value < -10 or value > 10:
            raise ValueError("invalid rate %s" % value)
        else:
            self._engine.Rate = value

    @property
    def volume(self):
        """ Return the current volume level """
        return self._engine.Volume

    @volume.setter
    def volume(self, value):
        """
        Chagne the volume of the voice

        value : int --- level of the volume to change to
        """
        if value < 0 or value > 100:
            raise ValueError("invalid volume %s" % value)
        else:
            self._engine.Volume = value
