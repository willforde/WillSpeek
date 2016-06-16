from pyxhook import HookManager
 
class Keylogger:
	def __init__(self):
		self.klg = HookManager()
		self.klg.KeyDown = self.listening
		self.klg.HookKeyboard()
		self.klg.start()
	
	def listening(self, event):
		k = event.Key
		print k
		
		if k == "space":
			k = " "
 
new = Keylogger()


"""
# Standard Library Imports
import os

# PyWin32 package imports
import win32gui_struct
import win32con
import win32gui

class SysTrayIcon(object):
	def __init__(self, menu_options, tray_name="willSpeak"):
		# Create instance level variable
		self.menu_options = menu_options
		
		# Create task mappings for try events
		message_map = {win32gui.RegisterWindowMessage("TaskbarCreated"): self.OnRestart,
					   win32con.WM_DESTROY: self.OnDestroy,
					   win32con.WM_COMMAND: self.OnCommand,
					   win32con.WM_USER+20: self.OnTaskbarNotify,}
		
		# Register the Window class.
		window_class = win32gui.WNDCLASS()
		window_class.lpszClassName = tray_name
		hinst = window_class.hInstance = win32gui.GetModuleHandle(None)
		window_class.style = win32con.CS_VREDRAW | win32con.CS_HREDRAW
		window_class.hCursor = win32gui.LoadCursor(0, win32con.IDC_ARROW)
		window_class.hbrBackground = win32con.COLOR_WINDOW
		window_class.lpfnWndProc = message_map
		classAtom = win32gui.RegisterClass(window_class)
		
		# Create the Window.
		style = win32con.WS_OVERLAPPED | win32con.WS_SYSMENU
		self.hwnd = win32gui.CreateWindow(classAtom, tray_name, style, 0, 0, win32con.CW_USEDEFAULT, win32con.CW_USEDEFAULT, 0, 0, hinst, None)
		win32gui.UpdateWindow(self.hwnd)
		self.notify_id = None
		self.create_icon()
		win32gui.PumpMessages()
	
	def create_icon(self, icon="icon.ico"):
		# If default icon exists, use it
		if os.path.isfile(icon):
			hinst = win32gui.GetModuleHandle(None)
			icon_flags = win32con.LR_LOADFROMFILE | win32con.LR_DEFAULTSIZE
			hicon = win32gui.LoadImage(hinst, icon, win32con.IMAGE_ICON, 0, 0, icon_flags)
		
		# No icon was found, using system default
		else:
			print "Can't find icon file - using default."
			hicon = win32gui.LoadIcon(0, win32con.IDI_APPLICATION)
		
		# Add icon to system tray
		if self.notify_id: message = win32gui.NIM_MODIFY
		else: message = win32gui.NIM_ADD
		
		# Create Tray and add to Taskbar
		flags = win32gui.NIF_ICON | win32gui.NIF_MESSAGE | win32gui.NIF_TIP
		self.notify_id = (self.hwnd, 0, flags, win32con.WM_USER+20, hicon, "willSpeak")
		try: win32gui.Shell_NotifyIcon(message, self.notify_id)
		except win32gui.error:
			# This is common when windows is starting, and this code is hit before the taskbar has been created.
			# When explorer starts, we get the TaskbarCreated message.
			print "Failed to add the taskbar icon - is explorer running?"
	
	def show_menu(self):
		# Create menu
		menu = win32gui.CreatePopupMenu()
		self.create_menu(menu, self.menu_options.menu_items())
		
		# Add menu to tray
		pos = win32gui.GetCursorPos()
		win32gui.SetForegroundWindow(self.hwnd)
		win32gui.TrackPopupMenu(menu, win32con.TPM_LEFTALIGN, pos[0], pos[1], 0, self.hwnd, None)
		win32gui.PostMessage(self.hwnd, win32con.WM_NULL, 0, 0)
	
	def create_menu(self, parent_menu, menu_options):
		"" Create Menus ""
		for key, (name, action) in menu_options.iteritems():
			# If action is dict, Create sub menu
			if isinstance(action, dict):
				submenu = win32gui.CreatePopupMenu()
				self.create_menu(submenu, action)
				item, _ = win32gui_struct.PackMENUITEMINFO(text=name, hSubMenu=submenu)
				win32gui.InsertMenuItem(parent_menu, 0, 1, item)
			
			# Else, create menu entry
			else:
				item, _ = win32gui_struct.PackMENUITEMINFO(text=name, wID=key)
				win32gui.InsertMenuItem(parent_menu, 0, 1, item)
	
	def OnRestart(self, hwnd, msg, wparam, lparam):
		"" This will recreate the tray icon if the windows explorer crashed ""
		self.create_icon()
	
	def OnTaskbarNotify(self, hwnd, msg, wparam, lparam):
		# Call OnActivate when tray icon is double clicked
		if lparam==win32con.WM_LBUTTONDBLCLK: self.menu_options.OnActivate(self)
		# Show menu when tray icon is right clicked
		elif lparam==win32con.WM_RBUTTONUP: self.show_menu()
		
		# Return True to indicate action completed successfully
		return True
	
	def OnCommand(self, hwnd, msg, wparam, lparam):
		id = win32gui.LOWORD(wparam)
		self.menu_options[id](self)
	
	def OnDestroy(self, hwnd, msg, wparam, lparam):
		nid = (self.hwnd, 0)
		win32gui.Shell_NotifyIcon(win32gui.NIM_DELETE, nid)
		win32gui.PostQuitMessage(0)
	
	def close(self):
		win32gui.DestroyWindow(self.hwnd)
"""