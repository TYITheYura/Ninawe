def RAWToPerOrPix(data, objectSize, fallback = None):
    data = str(data)

    try:
        if "%" in data:
            value = float(data.replace("%", ""))
            return round(int(objectSize) * (value / 100))
        elif "px" in data:
            return int(data.replace("px", ""))
        else:
            return int(data)
    except ValueError:
        if fallback:
            return fallback
        return 0
