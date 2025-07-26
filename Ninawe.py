#                  NI   E
#                  N N  E
#                  N  A E i n a w e
#                  N   WE ---------
#                Version: Very raw yet
# And remember guys: Ninawe is not a windows explorer

import tkinter as tk
import keyboard
import threading
import os
from PIL import Image, ImageTk
import glob
import ctypes
from ctypes import windll
import neofetch_win
import time
import configparser

class Config:
    def __init__(self):
        self.Resolution = None
        self.PanelBGColor = None
        self.PanelTextColor = None
        self.PanelMargin = None
        self.PanelDimensions = None
        self.WindowBGImage = None
        self.PanelRoundingRadius = None
        self.PanelAlpha = None
        self.Themes = []
        self.OnThemeCount = 0

    def Parse(self):
        config = configparser.ConfigParser()
        config.read("Configuration.ini")

        self.Resolution = self.GetResolution()

        # Window
        self.WindowBGImage = self.WindowBackgroundImageConfigure()
        
        # Panel
        self.PanelBGColor = config['Panel']['BGColor']
        self.PanelMargin = config.getfloat('Panel', 'Margin')
        self.PanelDimensions = self.PanelMarginConfigure()
        self.PanelRoundingRadius = config.getint('Panel', 'RoundingRadius')
        self.PanelAlpha = config.getfloat('Panel', 'Alpha')

        # Themes
        self.ThemeParse(config)

    def ThemeParse(self, config):
        for key, value in config['Themes'].items():
            color, text, image = [s.strip() for s in value.split(',')]
            self.Themes.append((color, text, image))

    def PanelMarginConfigure(self):
        ScreenWidth, ScreenHeight = self.Resolution

        MarginInPixels = int(ScreenWidth * self.PanelMargin)
        Width = ScreenWidth - 2 * MarginInPixels
        Height = int(ScreenHeight / 50)

        return Width, Height, MarginInPixels

    def GetResolution(self):
        user32 = ctypes.windll.user32
        return user32.GetSystemMetrics(0), user32.GetSystemMetrics(1)

    def WindowBackgroundImageConfigure(self, CustomDirectory = False):
        if CustomDirectory:
            file = glob.glob(CustomDirectory)
        else:
            file = glob.glob("background\\background.*")

        img = Image.open(file[0])
        img = self.ResizeAndCrop(img, self.Resolution)
        return img

    def ResizeAndCrop(self, img, target_size):
        target_w, target_h = target_size
        img_ratio = img.width / img.height
        target_ratio = target_w / target_h

        if img_ratio > target_ratio:
            scale = target_h / img.height
        else:
            scale = target_w / img.width

        new_size = (int(img.width * scale), int(img.height * scale))
        img = img.resize(new_size, Image.LANCZOS)

        left = (img.width - target_w) // 2
        top = (img.height - target_h) // 2
        right = left + target_w
        bottom = top + target_h

        return img.crop((left, top, right, bottom))

    def ApplyTheme(self, index):
        color, text, Image = self.Themes[index % len(self.Themes)]
        self.PanelBGColor = color
        self.PanelTextColor = text
        self.WindowBGImage = self.WindowBackgroundImageConfigure(Image)

    def SetTheme(self):
        self.OnThemeCount += 1
        self.ApplyTheme(self.OnThemeCount)
        self.UpdateAllWindows()

    def UpdateAllWindows(self):
        TaskPanel.ReConfigure()
        UserDesktop.ReConfigure()

class Panel:
    def __init__(self, master):
        self.root = tk.Toplevel(master)
        self.Visible = False
        self.TimeLabel = None

    def ReConfigure(self):
        self.root.geometry(
            f"{Config.PanelDimensions[0]}x{Config.PanelDimensions[1]}"
            f"+{Config.PanelDimensions[2]}+{Config.PanelDimensions[2]}"
        )
        self.root.configure(bg=Config.PanelBGColor)
        self.TimeLabel.configure(bg = Config.PanelBGColor, fg = Config.PanelTextColor)

    def Create(self):
        self.Toggle()
    
        self.TimeLabel = tk.Label(self.root, font=("System", 10))
        self.ReConfigure()

        self.TimeLabel.place(relx=0.5, rely=0.5, anchor="center")
        self.update_time()

        self.root.bind("<FocusOut>", lambda action: self.HideIfOutFocus())
        self.root.attributes("-topmost", True)
        self.root.overrideredirect(True)

        self.root.update_idletasks()
        self.RoundCorners(radius = Config.PanelRoundingRadius)

        self.root.attributes('-alpha', Config.PanelAlpha)

    def Toggle(self):
        if self.Visible:
            self.root.withdraw()
            print("hide")
            self.Visible = False
        else:
            self.root.deiconify()
            print("visible")
            self.root.focus_force()
            self.Visible = True
        

    def HideIfOutFocus(self):
        if self.Visible:
            print("out of focus")
            self.root.withdraw()
            self.Visible = False

    def RoundCorners(self, radius):
        self.hwnd = windll.user32.GetParent(self.root.winfo_id())
        region = windll.gdi32.CreateRoundRectRgn(
            0, 0,
            Config.PanelDimensions[0], Config.PanelDimensions[1],
            radius, radius)
        windll.user32.SetWindowRgn(self.hwnd, region, True)

    def update_time(self):
        current_time = time.strftime("%H:%M:%S")
        self.TimeLabel.config(text=current_time)
        self.root.after(1000, self.update_time)

class Window:
    def __init__(self):
        os.system("taskkill /f /im explorer.exe")
        self.root = tk.Tk()
        self.BackgroundLabel = tk.Label(self.root)

    def ReConfigure(self):
        self.root.geometry(f"{Config.Resolution[0]}x{Config.Resolution[1]}+0+0")
        self.BGImageTk = ImageTk.PhotoImage(Config.WindowBGImage)
        self.BackgroundLabel.config(image=self.BGImageTk)

    def Create(self):
        self.ReConfigure()
        self.root.overrideredirect(True)
        self.BackgroundLabel.place(x=0, y=0, relwidth=1, relheight=1)
        self.root.attributes("-disabled", True)
        self.root.attributes("-topmost", False)
        self.root.focus_force()
        self.root.mainloop()

class Hotkeys:
    def __init__(self):
        self.WinSolo = False
        self.ThemeCounter = 0

    def DoAction(self, action):
        ActionDict = dict(
            SHELL_CLOSE=lambda: (os.system("start explorer.exe"), os._exit(0)),
            START_TERMINAL=lambda: os.system(f"""start cmd /k "cls & echo. & neofetch --stdout --art {os.path.dirname(os.path.abspath(__file__))}\\background\\console\\console_logo.txt" """),
            START_PANEL=lambda: (),
            START_FM=lambda: os.system("start explorer.exe /n"),
            RECONFIGURE=lambda: (UserDesktop.ReConfigure(), TaskPanel.ReConfigure()),
            CHANGE_THEME=lambda: Config.SetTheme()
        )
        return ActionDict.get(action, lambda: None)()

    def hotkey_listener(self):
        def WinPressed(event):
            self.WinSolo = True

        def WinReleased(event):
            if self.WinSolo:
                TaskPanel.Toggle()

        def RandomPressed(event):
            if event.name not in ('left windows', 'right windows', "windows", "win"):
                self.WinSolo = False

        keyboard.add_hotkey('windows+q', lambda: self.DoAction("SHELL_CLOSE"))
        keyboard.add_hotkey('windows+t', lambda: self.DoAction("START_TERMINAL"))
        keyboard.add_hotkey('windows+p', lambda: self.DoAction("START_FM"))
        keyboard.add_hotkey('windows+a', lambda: self.DoAction("RECONFIGURE"))
        keyboard.add_hotkey('windows+u', lambda: self.DoAction("CHANGE_THEME"))
        keyboard.on_press_key('windows', WinPressed)
        keyboard.on_release_key('windows', WinReleased)

        keyboard.hook(RandomPressed)
        keyboard.wait()

Config = Config()
Config.Parse()

UserDesktop = Window()
HK = Hotkeys()
TaskPanel = Panel(UserDesktop.root)

threading.Thread(target=HK.hotkey_listener, daemon=True).start()
threading.Thread(target=TaskPanel.Create, daemon=True).start()

UserDesktop.Create()