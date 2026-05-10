import os
from core.config import ConfigWrapper
from core.config import config as selectedThemeConfig

class WidgetConfig:
    def __init__(self):
        self.WConfig = ConfigWrapper()

        self.widgetPath = os.path.dirname(os.path.abspath(__file__))
        self.configPath = os.path.join(self.widgetPath, "config.ini")

        self.selectedConfig = None

        self.propsSection = "Spectrum.Preferences"
        self.styleSection = "Spectrum.Style"

        # Important sh#t 🥀
        self.HARDWARE_ACCELERATION = selectedThemeConfig.app.GetBool("Performance", "hardware_acceleration", fallback = True)
        self.SAMPLE_RATE = 44100
        self.CHUNK_SIZE = 2048
        self.BANDS = 150
        self.MIN_FREQ = 40
        self.MAX_FREQ = 20000

        self.sensitivity = 3
        self.smoothing = 10
        self.refreshRateTimer = 33.3
        self.scale = "log"
        self.attackCoefficient = 0.5
        self.rollOffCoefficient = 0.5
        self.EQStartCoef = 1.5
        self.EQEndCoef = 1
        self.peakHoldsEnabled = False

        self.peakHoldsColor = "#FFFFFFFF"
        self.peakHoldsFalloff = 0.5
        self.peakHoldsHeight = 2
        self.paddings = 2
        self.color = "#FFFFFFFF"
        self.bandMinHeight = 1

        self.Updater()

    def Updater(self):
        self.WConfig.parser.read(self.configPath)

        # Config switcher
        if selectedThemeConfig.theme.GetSectionStatus(self.propsSection) and selectedThemeConfig.theme.GetSectionStatus(self.styleSection):
            self.selectedConfig = selectedThemeConfig.theme
        else:
            self.selectedConfig = self.WConfig

        self.HARDWARE_ACCELERATION = selectedThemeConfig.app.GetBool("Performance", "hardware_acceleration", fallback = True)

        self.widgetWidth = self.WConfig.GetInt("Layout", "min_width", fallback = 200)

        self.SAMPLE_RATE = self.selectedConfig.GetInt(self.propsSection, "sample_rate", fallback = 44100)
        self.CHUNK_SIZE = self.selectedConfig.GetInt(self.propsSection, "chunk_size", fallback = 2048)
        self.BANDS = max(min(self.selectedConfig.GetInt(self.propsSection, "bands", fallback = 64), self.widgetWidth), 0)
        self.MIN_FREQ = self.selectedConfig.GetInt(self.propsSection, "min_freq", fallback = 40)
        self.MAX_FREQ = self.selectedConfig.GetInt(self.propsSection, "max_freq", fallback = 20000)
        self.sensitivity = self.selectedConfig.GetFloat(self.propsSection, "sensitivity", fallback = 3)
        self.smoothing = self.selectedConfig.GetInt(self.propsSection, "smoothing", fallback = 10)
        self.physicsRefreshRateTimer = round(1000 / self.selectedConfig.GetInt(self.propsSection, "physics_refresh_rate", fallback = 30))
        self.refreshRateTimer = round(1000 / self.selectedConfig.GetInt(self.propsSection, "spectrum_refresh_rate", fallback = 30))
        self.scale = self.selectedConfig.Get(self.propsSection, "scale", fallback = "log").lower()
        self.attackCoefficient = self.selectedConfig.GetFloat(self.propsSection, "attack", fallback = 0.5)
        self.rollOffCoefficient = self.selectedConfig.GetFloat(self.propsSection, "roll_off", fallback = 0.5)
        self.EQStartCoef = self.selectedConfig.GetFloat(self.propsSection, "eq_start_coef", fallback = 1.0)
        self.EQEndCoef = self.selectedConfig.GetFloat(self.propsSection, "eq_end_coef", fallback = 1.5)
        self.peakHoldsEnabled = self.selectedConfig.GetBool(self.propsSection, "peak_holds_enabled", fallback = True)

        self.peakHoldsColor = self.selectedConfig.Get(self.styleSection, "peak_holds_color", fallback = "#FFFFFFFF")
        self.peakHoldsFalloff = self.selectedConfig.GetFloat(self.styleSection, "peak_holds_falloff", fallback = 0.5)
        self.peakHoldsHeight = self.selectedConfig.GetInt(self.styleSection, "peak_holds_height", fallback = 2)
        self.paddings = self.selectedConfig.GetInt(self.styleSection, "paddings", fallback = 2)
        self.color = self.selectedConfig.Get(self.styleSection, "color", fallback = "#FFFFFFFF")
        self.bandMinHeight = self.selectedConfig.GetFloat(self.styleSection, "band_min_height", fallback = 1)


WConfig = WidgetConfig()
