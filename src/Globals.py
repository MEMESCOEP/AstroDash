GL_VERSION_MAP = {
    1: "1.1",
    2: "2.0",
    3: "3.3",
    4: "4.3",
    5: "4.5",
    6: "4.6",
}

STATS_FILE = "GameStats.dat"
GAME_NAME = "AstroDash!"
STAR_SCALE_RANGE = (1.2, 2.6)
RESOURCE_USAGE_UPDATE_INTERVAL_MS = 250
SCORE_INCREASE_INTERVAL_MS = 100
TITLE_UPDATE_INTERVAL_MS = 500
STAR_UPDATE_INTERVAL_MS = 10
WINDOW_HEIGHT = 600
WINDOW_WIDTH = 800
LIFE_COUNT = 4
STAR_COUNT = 115
fullscreenMode = False
enableDebug = False
enableVSync = True
deltaTime = 0.0
frameCount = 0
highScore = 0
livesLeft = LIFE_COUNT
score = 0
FPS = 0

def IsPointInsideRect(pointVec2, x, y, width, height):
    return x <= pointVec2.x <= x + width and y <= pointVec2.y <= y + height
