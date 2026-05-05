import os
import sys

# Absolute path to files
if getattr(sys, "frozen", False):
    # Compiled
    BASE_DIR = os.path.dirname(sys.executable)
else:
    # Non-compiled
    # from config.py to default directory (.. x 4 lol)
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

def MakeLog(section = "", infoText = "", clearLogs = False):
    if clearLogs:
        with open(f"{BASE_DIR}\\userdata\\logs\\logfile.txt", "w", encoding = "utf-8") as logFile:
            return

    message = ""

    if len(infoText) == 0:
        message = section
    else:
        message = f"{section} | {infoText}"

    with open(f"{BASE_DIR}\\userdata\\logs\\logfile.txt", "a", encoding = "utf-8") as logFile:
        logFile.write(message + "\n")
    print(message)

def MakeLogExtra(section = "", infoText = "", clearLogs = False):
    if clearLogs:
        with open("C:\\logfile.txt", "w", encoding = "utf-8") as logFile:
            return

    message = ""

    if len(infoText) == 0:
        message = section
    else:
        message = f"{section} | {infoText}"

    with open("C:\\logfile.txt", "a", encoding = "utf-8") as logFile:
        logFile.write(message + "\n")
    print(message)
