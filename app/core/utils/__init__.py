from .logger import MakeLog
from .helpers import LoadFont
from .winapi import *

import win32com.client
WSHELL = win32com.client.Dispatch("WScript.Shell")
