from .logger import MakeLog, MakeLogExtra
from .helpers import LoadFont, GetRealTargetPath
from .winapi import *
from .percenttopix import RAWToPerOrPix
from .internalwindowsanimation import InternalWindowFader
# from .externalwindowsanimation import ExternalWindowFader, ACTIVE_ANIMATIONS

import win32com.client
WSHELL = win32com.client.Dispatch("WScript.Shell")
