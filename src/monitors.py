# Standard library imports
from tkinter import Tk, TclError
import asyncio

# Queue of text strings to convert to speech
speakQ = asyncio.Queue()

# Clipboard monitor setup
gui = Tk()
gui.withdraw()

async def clipboard():
    prev_text = None
    while True:
        # Check the clipboard for data
        try:
            clipboard_text = gui.clipboard_get()
        except TclError:
            await asyncio.sleep(1)
            continue

        if prev_text is None:
            prev_text = clipboard_text

        elif clipboard_text and not clipboard_text == prev_text:
            prev_text = clipboard_text
            await speakQ.put(clipboard_text)

        # Sleep for 50ms in order to loop 20 times a second
        await asyncio.sleep(.05)
