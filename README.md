[![Donate](https://img.shields.io/badge/Donate-PayPal-green.svg)](https://www.paypal.com/cgi-bin/webscr?cmd=_donations&business=SLQMJBWX7G2PU)

# WillSpeek
Python Text to Speach using Sapi5 with server / client model

Very much a work in progress.

# Info
I created this project as a way to have good TTS on linux, because TTS on linux at the moment is dreadful. For a long time I wanted to switch to linux but I needed a good linux TTS software but could not find one.
So I decided to create this project to interface with the windows SAPI5 TTS engine. How I have it working is by running this software in server mode on a windows 10 virtual machine on my network and then configuring the linux client to communicate with the windows side TTS server. Then the client will monitor the clipboard for text that was copied and will convert it into speech. Will work on both windows and linux, maybe even mac.

# Dependencies
On Windows:
* pyWin32
* comtypes

Linux:
* Tkinter

Both:
* pyaudio


# TODO
* A lot
* Setup the server to send back the wav file in a seperate socket thats dedicated to sending audio only.
* Improve the client side code to handle reconnection to server when the connection drops.
* Find a better way to communicate with the server.

## Version
0.0.1

## Licence
Not sure yet
