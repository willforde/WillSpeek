#!/usr/bin/env python2
# Standard Library Imports
import Queue
import functools
import re
import threading
import time

# Python 3 Safe
import Tkinter as tk  # Python2

# Package imports
from api.sapiRemote import TTSClient
# from api.sapiLocal import TTSClient
from api import audio

# Setup Speach engine
tts = TTSClient()
tts.volume = 100
tts.rate = 3

# Setup Queues
speachQueue = Queue.Queue()
audio.speachQueue = speachQueue
lock = threading.Lock()
audio.tts = tts

# Striper for Read more at:
readMore = re.compile("([Rr]ead more\s*[at]*:*\s+http\S+|[Ss]ee more at:*\s+http\S+)")


def clipboard_processor():
    while True:
        # Fetch Clipboard content
        text = speachQueue.get()
        tts.speek(text.encode("utf8"))
        speachQueue.task_done()


class ClipboardMonitor(object):
    """ Class to monitor clipboard changes """

    def __init__(self):
        # Initialize Clipboard Processor
        t = threading.Thread(target=clipboard_processor)
        t.daemon = True
        t.start()

        # Setup clipboard access
        self.gui = tk.Tk()
        self.gui.withdraw()
        self.running = True
        self.enabled = True

        # Welcome the user
        tts.speek("Welcome to will speek!")

    def monitor(self):
        """ Monitor clipboard for changes """
        prev = None
        while self.running:
            if self.enabled:
                # Check the clipboard for data
                data = self.get_clipboard_text()
                if prev is None:
                    prev = data

                elif data and not data == prev:
                    prev = data

                    # Search for readMore text
                    remove_text = readMore.findall(data)
                    for text in remove_text:
                        data = data.replace(text, u"")

                    for part in data.strip().replace(u"\r\n", u"\n").split(u"\n\n"):
                        speachQueue.put(part)

            elif prev:
                prev = None

            # Sleep for 50ms in order to loop 20 times a second
            time.sleep(.05)

    def get_clipboard_text(self):
        try:
            return self.gui.clipboard_get()
        except Exception:
            time.sleep(.5)
            return False

    def set_voice(self, voice_name):
        """ Set a voice by name """
        for voice in tts.get_voices():
            if voice_name.lower() in voice.name.lower():
                tts.voice = voice

    def close(self):
        with lock:
            self.running = False


class MenuItems(object):
    def __init__(self):
        self.commands = {}

    def menu_items(self):
        items = [(1024, "Quit", self.OnQuit),
                 (1025, "Stop", self.OnStop),
                 (1050, "Disable", self.OnDisable) if monitor.enabled else (1051, "Enable", self.OnEnable),
                 (1026, "Voices", self.voices),
                 (1036, "Rate %s" % tts.rate, self.rates),
                 (1039, "Volume %s" % tts.volume, self.volume)]

        # Register the menu items and return them
        return self.register_menu_items(items)

    @property
    def voices(self):
        menu = list()
        keyID = 1027
        for voice in tts.get_voices():
            item = (keyID, voice.name.split(" ", 2)[1], functools.partial(self.OnVoice, voice))
            menu.append(item)
            keyID += 1
        return menu

    @property
    def rates(self):
        menu = list()
        menu.append((1038, "Increase", self.OnRateIncrease))
        menu.append((1037, "Decrease", self.OnRateDecrease))
        return menu

    @property
    def volume(self):
        menu = list()
        menu.append((1041, "Increase", self.OnVolumeIncrease))
        menu.append((1040, "Decrease", self.OnVolumeDecrease))
        return menu

    def register_menu_items(self, items):
        menu = dict()
        for key, name, action in items:
            if isinstance(action, list) or isinstance(action, tuple):
                menu[key] = (name, self.register_menu_items(action))
            else:
                if not key in self.commands: self.commands[key] = action
                menu[key] = (name, action)

        # Return menu ready to be displayed
        return menu

    def __getitem__(self, key):
        return self.commands[key]

    def OnActivate(self, sysTray):
        """ When tray icon is double clicked, stop speaking """
        self.OnStop(sysTray)

    def OnQuit(self, sysTray):
        sysTray.close()
        monitor.close()

    def OnStop(self, sysTray):
        audio.stop()
        tts.stop()

    def OnVoice(self, voice, sysTray):
        tts.voice = voice

    def OnRateIncrease(self, sysTray):
        if tts.rate < 10: tts.rate += 1

    def OnRateDecrease(self, sysTray):
        if tts.rate > -10: tts.rate -= 1

    def OnVolumeIncrease(self, sysTray):
        if tts.volume < 100: tts.volume += 10

    def OnVolumeDecrease(self, sysTray):
        if tts.volume > 0: tts.volume -= 10

    def OnDisable(self, sysTray):
        monitor.enabled = False

    def OnEnable(self, sysTray):
        monitor.enabled = True


# Monitor for clipboard changes
monitor = ClipboardMonitor()
monitor.monitor()
