from pyray import Vector2, draw_texture_ex, WHITE, GREEN, RED, draw_circle_v
from AnimatedSprite import AnimatedSprite
import Globals
import random

class Meteor:
    def __init__(self, xPos, yPos, moveSpeedX, moveSpeedY):
        self.scale = 0.2
        self.position = Vector2(xPos, yPos)
        self.moveSpeedX = moveSpeedX
        self.moveSpeedY = moveSpeedY
        self.animation = AnimatedSprite()
        self.animation.AddSprites("Assets/Animations/Meteor")
        self.animation.indexSwitchFreq = 100
        self.leftBoundary = 0

    def Move(self, delta, cameraTargetX, playerPosition):
        self.position.x -= self.moveSpeedX * delta
        self.position.y += self.moveSpeedY * delta

        if Globals.livesLeft <= 0:
                return

        isInXRange = self.position.x < playerPosition.x + 24 and self.position.x > playerPosition.x - 24
        isInYRange = self.position.y < (Globals.WINDOW_HEIGHT - playerPosition.y + 24) and self.position.y > (Globals.WINDOW_HEIGHT - playerPosition.y - 24)
        hitPlayer = isInXRange and isInYRange

        if self.position.y > Globals.WINDOW_HEIGHT + 16 or hitPlayer:
            self.position.x = cameraTargetX + Globals.WINDOW_WIDTH + random.randint(10, 100)
            self.position.y = random.randint(10, 500)
            self.moveSpeedX = random.randint(100, 200)
            self.moveSpeedY = random.randint(75, 125)

            if hitPlayer:
                Globals.livesLeft -= 1

    def Draw(self, delta):
        draw_texture_ex(self.animation.GetNextSprite(delta), Vector2(self.position.x - 8, self.position.y - 16), 0.0, self.scale, WHITE)
