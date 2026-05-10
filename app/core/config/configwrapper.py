import configparser
import os
import hashlib
from . import BASE_DIR
from core.utils import MakeLog

MakeLog(clearLogs = True)
MakeLog(f"[Log] [Config] | Default path: {BASE_DIR}")

# Base class for convenient data retrieval
class ConfigWrapper:
    def __init__(self):
        self.parser = configparser.ConfigParser(interpolation = None)

    #
    #   Getters
    #

    def Get(self, section, option, fallback = None):
        try:
            return self.parser.get(section, option, fallback = fallback)
        except (configparser.NoSectionError, configparser.NoOptionError):
            return fallback

    def GetBool(self, section, option, fallback = False):
        try:
            return self.parser.getboolean(section, option, fallback = fallback)
        except (configparser.NoSectionError, configparser.NoOptionError, Exception):
            return fallback

    def GetInt(self, section, option, fallback = 0):
        try:
            return self.parser.getint(section, option)
        except ValueError:
            # Attempt to read only numeric data if it exists
            try:
                rawData = self.parser.get(section, option)
                numData = rawData.replace("px", "").replace("%", "").strip()
                return int(numData)
            except ValueError:
                return fallback
        except Exception:
            return fallback

    def GetFloat(self, section, option, fallback = 0.00):
        try:
            return self.parser.getfloat(section, option)
        except ValueError:
            # Attempt to read only numeric data if it exists
            rawData = self.parser.get(section, option)
            numData = rawData.replace("px", "").replace("%", "").strip()
            return int(numData)
        except Exception:
            return fallback

    def GetList(self, section, option, fallback = []):
        try:
            rawData = self.parser.get(section, option)
            return [line.strip() for line in rawData.split('\n') if line.strip()]
        except Exception:
            return fallback

    def GetPathList(self, section, option, fallback = []):
        try:
            lines = self.GetList(section, option, fallback = fallback)
            return [os.path.expandvars(line) for line in lines]
        except Exception:
            return fallback

    def GetSectionStatus(self, section):
        return self.parser.has_section(section)

    def GetPath(self, path = ""):
        return os.path.join(BASE_DIR, path)

    #
    #   Setters
    #

    def Set(self, section, option, value):
        if not self.parser.has_section(section):
            self.parser.add_section(section)
        self.parser.set(section, str(option), str(value.replace("|", "\n")))

    def Save(self, filePath = None):
        if filePath == "theme":
            filePath = getattr(self, "themeInitFile", None)
        elif filePath == "app":
            filePath = getattr(self, "configFilePath", None)

        if filePath:
            try:
                with open(filePath, "w", encoding = "utf-8") as configfile:
                    self.parser.write(configfile)
                MakeLog("[Log] [Config]", f"Saved to: {filePath}")
                return True
            except Exception as e:
                MakeLog("[Log] [Config]", f"Failed to save {filePath}: {e}")
        return False

    #
    #   Checkers
    #   I'm too dumb to do this properly, so the hash variable must be called "hashes" in any case
    #

    def SectionHashCheck(self, dataClaimer = None):
        if dataClaimer is None:
            MakeLog("[Log] [ConfigWrapper] [SectionHashCheck] | Data not set")
            return

        changedSections = []
        allSections = dataClaimer.parser.sections()

        for section in allSections:
            items = sorted(dataClaimer.parser.items(section))
            rawData = str(items).encode("utf-8")
            currentHash = hashlib.md5(rawData).hexdigest()
            oldHash = dataClaimer.hashes.get(section)

            if currentHash != oldHash:
                dataClaimer.hashes[section] = currentHash
                changedSections.append(section)

        return changedSections
