from .logger import MakeLog
from .helpers import LoadFont
from .winapi import *
from .percenttopix import RAWToPerOrPix

import win32com.client
WSHELL = win32com.client.Dispatch("WScript.Shell")
