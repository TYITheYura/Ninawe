import sys
import os

# Absolute path to files
if getattr(sys, "frozen", False):
    # Compiled
    BASE_DIR = os.path.dirname(sys.executable)
else:
    # Non-compiled
    # from config.py to default directory (.. x 4 lol)
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from .configwrapper import ConfigWrapper
from .globalthemeconfig import GlobalThemeConfigData
from .appconfig import AppConfig
from .themeconfig import ThemeConfig
from .configupdatechecker import ConfigUpdateChecker
from core.managers import ConfigManager

config = ConfigManager(AppConfig(), ThemeConfig())
