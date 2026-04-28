import win32gui
import pywintypes
from core.utils import MakeLog

def SetFocus(hwnd):
	#
	#  Additional ! FOCUS ! control via winapi if PyQt can't handle it
	#               🗝 🗝
	#               🗝 🗝
	#               🗝 🗝
	#               🗝 🗝
	#
	hwnd = int(hwnd)

	try:
		win32gui.SetForegroundWindow(hwnd)
	except pywintypes.error as e:
		MakeLog("[Log] [SetFocus]", f"SetForegroundWindow failed: {e}")

		try:
			win32gui.BringWindowToTop(hwnd)
		except Exception:
			MakeLog("[Log] [SetFocus]", f"BringWindowToTop failed: {e}")

		try:
			if hasattr(win32gui, 'SetActiveWindow'):
				win32gui.SetActiveWindow(hwnd)
		except Exception:
			MakeLog("[Log] [SetFocus]", f"SetActiveWindow failed: {e}")
