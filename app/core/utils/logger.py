from core.config import BASE_DIR

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
