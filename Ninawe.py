#                  NI   E
#                  N N  E
#                  N  A E i n a w e
#                  N   WE ---------
#                 Version: Very RAW3
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

class Effects:
    def __init__(self):
        self.AnimationSteps = 0
        self.AnimationDelay = 0
        self.HalfSteps = 0
        self.HalfDelay = 0

    def Update(self):
        self.AnimationSteps = round(Config.AnimationDuration * Config.AnimationFrames)
        self.AnimationDelay = round((1000 * Config.AnimationDuration) / self.AnimationSteps)
        self.HalfSteps = round(self.AnimationSteps / 2)
        self.HalfDelay = round(self.AnimationDelay / 2)
    
    def Hide(self, ObjectsPreferences, Action, half = False, step = None):
        steps = self.HalfSteps if half else self.AnimationSteps
        delay = self.HalfDelay if half else self.AnimationDelay
        if step is None:
            step = steps

        Alpha = step / steps
        for ObjectPreference in ObjectsPreferences:
            for Object, AlphaMultiplier in ObjectPreference:
                Object.root.attributes('-alpha', Alpha * AlphaMultiplier)
        if step > 0:
            UserDesktop.root.after(delay, lambda: self.Hide(ObjectsPreferences, Action, half, step - 1))
        else:
            Action()

    def Show(self, ObjectsPreferences, Action, half = False, step = 0):
        steps = self.HalfSteps if half else self.AnimationSteps
        delay = self.HalfDelay if half else self.AnimationDelay

        Alpha = step / steps
        for ObjectPreference in ObjectsPreferences:
            for Object, AlphaMultiplier in ObjectPreference:
                Object.root.attributes('-alpha', Alpha * AlphaMultiplier)
        if step < steps:
            UserDesktop.root.after(delay, lambda: self.Show(ObjectsPreferences, Action, half, step + 1))
        else:
            Action()

class Configs:
    def __init__(self):
        self.Resolution = None
        self.PanelBGColor = None
        self.PanelTextColor = None
        self.PanelMargin = None
        self.PanelDimensions = None
        self.WindowDefaultBGImagePath = None
        self.WindowBGImage = None
        self.PanelRoundingRadius = None
        self.PanelAlpha = None
        self.Themes = []
        self.OnThemeCount = 0
        self.AnimationFrames = 0
        self.AnimationDuration = 0
        self.HotkeysList = []
        self.ExitKey = None
        self.ChangeThemeKey = None
        self.ReConfigureKey = None
        self.PanelKey = None
        self.DefaultHKActions = {
            "startfilemanager": "START_FM",
            "startterminal": "START_TERMINAL"
        }

    def Parse(self):
        config = configparser.ConfigParser()
        config.read("Configuration.ini")

        self.Resolution = self.GetResolution()

        # Window
        self.WindowDefaultBGImagePath = config['Window']['BackgroundImage']
        self.WindowBGImage = self.WindowBackgroundImageConfigure()
        
        # Panel
        self.PanelBGColor = config['Panel']['BGColor']
        self.PanelMargin = config.getfloat('Panel', 'Margin')
        self.PanelDimensions = self.PanelMarginConfigure()
        self.PanelRoundingRadius = config.getint('Panel', 'RoundingRadius')
        self.PanelAlpha = config.getfloat('Panel', 'Alpha')
        self.PanelTextColor = config['Panel']['TextColor']
        
        # Preferences
        self.AnimationDuration = config.getfloat('Preferences', 'AnimationDuration')
        self.AnimationFrames = config.getint('Preferences', 'AnimationFrames')
        
        # Themes
        self.ThemeParse(config)

        # Hotkeys
        self.ExitKey = config['NinaweHotkeys']['NinaweQuit']
        self.ChangeThemeKey = config['NinaweHotkeys']['NinaweChangeTheme']
        self.ReConfigureKey = config['NinaweHotkeys']['NinaweReconfigure']
        self.PanelKey = config['NinaweHotkeys']['NinawePanel']

        self.HotkeyParse(config)

    def HotkeyParse(self, config):
        self.HotkeysList.clear()
        for key, value in config['CustomHotkeys'].items():
            combo, action = [s.strip() for s in value.split(',')]

            if key.lower() in self.DefaultHKActions and action == "default":
                action = lambda key = key: HK.DoAction(self.DefaultHKActions[key])
            else:
                action = lambda action = action: os.system(action)

            self.HotkeysList.append((combo, action))

    def ThemeParse(self, config):
        self.Themes.clear()
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
            file = glob.glob(self.WindowDefaultBGImagePath)

        img = Image.open(file[0])
        img = self.ResizeAndCrop(img, self.Resolution)
        return img

    def ResizeAndCrop(self, img, TargetSize):
        TargetWidth, TargetHeight = TargetSize
        ImgRatio = img.width / img.height
        target_ratio = TargetWidth / TargetHeight

        if ImgRatio > target_ratio:
            Scale = TargetHeight / img.height
        else:
            Scale = TargetWidth / img.width

        NewSize = (int(img.width * Scale), int(img.height * Scale))
        img = img.resize(NewSize, Image.LANCZOS)

        Left = (img.width - TargetWidth) // 2
        Top = (img.height - TargetHeight) // 2
        Right = Left + TargetWidth
        Bottom = Top + TargetHeight

        return img.crop((Left, Top, Right, Bottom))

    def SetDefaultTheme(self, color, text, image):
        config = configparser.ConfigParser()
        config.read('Configuration.ini')

        config.set('Window', 'BackgroundImage', image)
        config.set('Panel', 'BGColor', color)
        config.set('Panel', 'TextColor', text)

        with open('Configuration.ini', 'w') as EditedDefaultTheme:
            config.write(EditedDefaultTheme)

    def ApplyTheme(self, index):
        color, text, Image = self.Themes[index % len(self.Themes)]
        self.SetDefaultTheme(color, text, Image)
        self.PanelBGColor = color
        self.PanelTextColor = text
        self.WindowBGImage = self.WindowBackgroundImageConfigure(Image)

    def SetTheme(self):
        self.ApplyTheme(self.OnThemeCount)
        self.UpdateAllWindows()
        self.OnThemeCount += 1

    def UpdateAllWindows(self):
        WindowEffects.Hide(
            [
                [(TaskPanel, self.PanelAlpha)],
                [(UserDesktop, 1)]
            ],
            lambda: [
                TaskPanel.ReConfigure(),
                UserDesktop.ReConfigure(),
                WindowEffects.Show(
                    [
                        [(TaskPanel, self.PanelAlpha)],
                        [(UserDesktop, 1)]
                    ],
                    lambda: None, True
                )
            ], True
        )

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
            self.Visible = False
        else:
            self.root.deiconify()
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
        self.PanelKeyAltName = None
        self.KeyAlts = [
            ["alt", "left alt", "right alt", "alt gr", "menu"],
            ["ctrl", "left ctrl", "right ctrl", "control"],
            ["shift", "left shift", "right shift"],
            ["win", "windows", "left windows", "right windows"],
            ["fn", "function"],
            ["caps lock", "capslock"],
            ["tab", "tabulator"],
            ["esc", "escape"],
        ]

    def DoAction(self, action):
        ActionDict = dict(
            SHELL_CLOSE=lambda: (os.system("start explorer.exe"), os._exit(0)),
            START_TERMINAL=lambda: os.system(f"""start cmd /k "cls & echo. & neofetch --stdout --art {os.path.dirname(os.path.abspath(__file__))}\\background\\console\\console_logo.txt" """),
            START_FM=lambda: os.system("start explorer.exe /n"),
            RECONFIGURE=lambda: (
                Config.Parse(),
                WindowEffects.Update(),
                UserDesktop.ReConfigure(),
                TaskPanel.ReConfigure(),
                keyboard.clear_all_hotkeys(),
                HK.InitHotkeys()
                ),
            CHANGE_THEME=lambda: Config.SetTheme()
        )
        return ActionDict.get(action, lambda: None)()

    def InitHotkeys(self):

        keyboard.add_hotkey(Config.ExitKey, lambda: self.DoAction("SHELL_CLOSE"))
        keyboard.add_hotkey(Config.ReConfigureKey, lambda: self.DoAction("RECONFIGURE"))
        keyboard.add_hotkey(Config.ChangeThemeKey, lambda: self.DoAction("CHANGE_THEME"))
        
        for combo, action in Config.HotkeysList:
            keyboard.add_hotkey(combo, lambda action = action: action())

        self.PanelKeyAltName = [keys.strip() for keys in Config.PanelKey.split(",")]

        for Alts in self.KeyAlts:
            if Config.PanelKey.lower() in Alts:
                self.PanelKeyAltName = Alts
                break

    def hotkey_listener(self):
        def handle_event(event):
            KeyName = event.name.lower()

            IsPanelKey = (
                KeyName == Config.PanelKey.lower()
                or KeyName in self.PanelKeyAltName
            )

            if event.event_type == "down":
                if IsPanelKey:
                    self.WinSolo = True
                else:
                    self.WinSolo = False

            elif event.event_type == "up":
                if IsPanelKey and self.WinSolo:
                    TaskPanel.Toggle()
                else:
                    self.WinSolo = False

        keyboard.hook(handle_event)
        keyboard.wait()

Config = Configs()
WindowEffects = Effects()
UserDesktop = Window()
TaskPanel = Panel(UserDesktop.root)
HK = Hotkeys()

Config.Parse()
WindowEffects.Update()
HK.InitHotkeys()

threading.Thread(target=HK.hotkey_listener, daemon=True).start()
threading.Thread(target=TaskPanel.Create, daemon=True).start()

UserDesktop.Create()