from PyQt6.QtCore import QRect

class GridManager:
    @staticmethod
    def GetMaxCols(windowWidth, DConfig, IConfig):
        return max(1, (windowWidth - DConfig.windowMarginX * 2) // (IConfig.itemWidth + IConfig.spacingX))

    @staticmethod
    def GetMaxRows(windowHeight, DConfig, IConfig):
        return max(1, (windowHeight - DConfig.windowMarginY * 2) // (IConfig.itemHeight + IConfig.spacingY))

    @staticmethod
    def PixelsToGrid(pixelX, pixelY, DConfig, IConfig):
        gridX = round((pixelX - DConfig.windowMarginX) / (IConfig.itemWidth + IConfig.spacingX))
        gridY = round((pixelY - DConfig.windowMarginY) / (IConfig.itemHeight + IConfig.spacingY))
        return max(0, gridX), max(0, gridY)

    @staticmethod
    def GridToPixels(gridX, gridY, DConfig, IConfig):
        posX = DConfig.windowMarginX + gridX * (IConfig.itemWidth + IConfig.spacingX)
        posY = DConfig.windowMarginY + gridY * (IConfig.itemHeight + IConfig.spacingY)
        return int(posX), int(posY)

    @staticmethod
    def CalculateHintGeometry(gridX, gridY, spanX, spanY, DConfig, IConfig):
        pixelWidth = (spanX * IConfig.itemWidth) + ((spanX - 1) * IConfig.spacingX)
        pixelHeight = (spanY * IConfig.itemHeight) + ((spanY - 1) * IConfig.spacingY)

        posX, posY = GridManager.GridToPixels(gridX, gridY, DConfig, IConfig)
        return QRect(posX, posY, int(pixelWidth), int(pixelHeight))

    @staticmethod
    def IsPositionFree(startX, startY, spanX, spanY, occupiedPositions, maxCols, maxRows):
        if startY + spanY > maxRows or startX + spanX > maxCols:
            return False

        for x in range(startX, startX + spanX):
            for y in range(startY, startY + spanY):
                if (x, y) in occupiedPositions:
                    return False
        return True

    @staticmethod
    def GetFirstFreePosition(occupiedPositions, maxCols, maxRows, spanX = 1, spanY = 1):
        col = 0
        while col + spanX <= maxCols:
            for row in range(maxRows - spanY + 1):
                if GridManager.IsPositionFree(col, row, spanX, spanY, occupiedPositions, maxCols, maxRows):
                    return [col, row]
            col += 1

        return None

    @staticmethod
    def IsPositionValid(targetGridX, targetGridY, itemSpanX, itemSpanY, ignoreItems, desktopItems, windowWidth, windowHeight, DConfig, IConfig):
        maxCols = GridManager.GetMaxCols(windowWidth, DConfig, IConfig)
        maxRows = GridManager.GetMaxRows(windowHeight, DConfig, IConfig)

        if targetGridX < 0 or targetGridY < 0 or targetGridX + itemSpanX > maxCols or targetGridY + itemSpanY > maxRows:
            return False

        for otherItem in desktopItems:
            if otherItem in ignoreItems:
                continue

            otherX = otherItem.gridX
            otherY = otherItem.gridY

            if otherX == -1 or otherY == -1:
                continue

            if (
                targetGridX < otherX + otherItem.spanX and
                targetGridX + itemSpanX > otherX and
                targetGridY < otherY + otherItem.spanY and
                targetGridY + itemSpanY > otherY
            ):
                return False

        return True
