from pyray import load_texture
import os

class AnimatedSprite:
    def __init__(self):
        self.sprites = []
        self.spriteCount = 0
        self.spriteIndex = 0
        self.indexSwitchTime = 0
        self.indexSwitchFreq = 125
        self.animTime = 0

    def AddSprites(self, spriteDirectory):
        # List all files, sort them alphabetically
        files = sorted(os.listdir(spriteDirectory))

        for item in files:
            spritePath = os.path.join(spriteDirectory, item)

            if os.path.isfile(spritePath):
                newTexture = load_texture(spritePath)
                assert newTexture.id != 0, f"Failed to load sprite \"{spritePath}\"!"

                self.sprites.append(newTexture)
                self.spriteCount += 1

    def GetNextSprite(self, deltaTime):
        self.animTime += deltaTime
        sprite = self.sprites[self.spriteIndex]

        if self.animTime >= self.indexSwitchTime:
            self.indexSwitchTime = self.animTime + (self.indexSwitchFreq / 1000)
            self.spriteIndex = (self.spriteIndex + 1) % self.spriteCount

        return sprite
