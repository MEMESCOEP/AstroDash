from pyray import *
import AnimatedSprite
import Globals
import Physics
import pymunk
import pyray

PLAYER_SPAWN_POS = (30, 60)
PLAYER_RIGHT_KEY = pyray.KeyboardKey.KEY_D
PLAYER_LEFT_KEY = pyray.KeyboardKey.KEY_A
PLAYER_HEIGHT = 40
PLAYER_WIDTH = 20
moveSpeed = 150
jumpForce = 250
playerBody = None
wallRight = False
wallLeft = False
grounded = False
walkingAnimation = None
idleAnimation = None
lastDirection = 0
renderScale = 0.3

def HandleGroundCollisions(arbiter, space, data):
    global grounded

    if arbiter.shapes[1].collision_type != Physics.CollisionLayers.GROUND.value:
        return True

    grounded = True
    return True

def EndGroundCollisions(arbiter, space, data):
    global grounded

    if arbiter.shapes[1].collision_type != Physics.CollisionLayers.GROUND.value:
        return True

    grounded = False
    return True

def HandleWallCollisions(arbiter, space, data):
    global wallRight, wallLeft

    player = arbiter.shapes[0].body
    vx, vy = player.velocity
    wallLeft = vx < 0
    wallRight = vx > 0

    return True

def EndWallCollisions(arbiter, space, data):
    global wallRight, wallLeft

    wallLeft = False
    wallRight = False

    return True

def Init():
    global playerBody, walkingAnimation, idleAnimation

    # Create the player body and the wall & ground sensors
    playerBody = Physics.CreatePhysicsBody(PLAYER_SPAWN_POS[0], PLAYER_SPAWN_POS[1], PLAYER_WIDTH, PLAYER_HEIGHT, Physics.MaterialTypes.CONCRETE_DRY, instantAdd=True)
    groundSensor = pymunk.Segment(
        playerBody,
        ((-PLAYER_WIDTH / 2) + 2, (-PLAYER_HEIGHT / 2) - 2),
        ((PLAYER_WIDTH / 2) - 2, (-PLAYER_HEIGHT / 2) - 2),
        1
    )

    rightWallSensor = pymunk.Segment(
        playerBody,
        ((PLAYER_WIDTH / 2) + 4, (-PLAYER_HEIGHT / 2) + 8),
        ((PLAYER_WIDTH / 2) + 4, (PLAYER_HEIGHT / 2) - 2),
        1
    )

    leftWallSensor = pymunk.Segment(
        playerBody,
        ((-PLAYER_WIDTH / 2) - 4, (-PLAYER_HEIGHT / 2) + 8),
        ((-PLAYER_WIDTH / 2) - 4, (PLAYER_HEIGHT / 2) - 2),
        1
    )

    # Configure the sensors
    groundSensor.sensor = True
    rightWallSensor.sensor = True
    leftWallSensor.sensor = True
    groundSensor.collision_type = Physics.CollisionLayers.GROUND.value
    rightWallSensor.collision_type = Physics.CollisionLayers.WALL.value
    leftWallSensor.collision_type = Physics.CollisionLayers.WALL.value

    # Add the sensors to the physics world
    Physics.physWorld.add(rightWallSensor)
    Physics.physWorld.add(leftWallSensor)
    Physics.physWorld.add(groundSensor)

    # Add the collision handlers for the ground and wall sensors
    groundHandler = Physics.physWorld.add_collision_handler(Physics.CollisionLayers.DEFAULT.value, Physics.CollisionLayers.GROUND.value)
    wallHandler = Physics.physWorld.add_collision_handler(Physics.CollisionLayers.WALL.value, Physics.CollisionLayers.GROUND.value)

    # Set collision callbacks
    groundHandler.begin = HandleGroundCollisions
    wallHandler.begin = HandleWallCollisions
    groundHandler.separate = EndGroundCollisions
    wallHandler.separate = EndWallCollisions

    # Load the animations
    walkingAnimation = AnimatedSprite.AnimatedSprite()
    idleAnimation = AnimatedSprite.AnimatedSprite()
    walkingAnimation.AddSprites("Assets/Animations/PlayerWalk")
    idleAnimation.AddSprites("Assets/Animations/PlayerIdle")

def Movement(delta):
    global lastDirection
    vx, vy = playerBody.velocity

    if Globals.livesLeft > 0:
        moveRight = pyray.is_key_down(PLAYER_RIGHT_KEY) and wallRight == False
        moveLeft = pyray.is_key_down(PLAYER_LEFT_KEY) and wallLeft == False

        if moveRight == True and moveLeft == False:
            vx = moveSpeed
            lastDirection = 1

        elif moveRight == False and moveLeft == True:
            vx = -moveSpeed
            lastDirection = -1

        else:
            vx = Globals.Lerp(vx, 0, 10 * delta)

        if grounded == True and pyray.is_key_pressed(pyray.KeyboardKey.KEY_SPACE):
                vy = jumpForce

    if playerBody.position.x < PLAYER_WIDTH:
        vx = max(vx, 0)

    playerBody.velocity = (vx, vy)
    playerBody.moment = float('inf') # Stops body rotation

def Health():
    if playerBody.position.y < -PLAYER_HEIGHT:
        Globals.livesLeft = 0
        playerBody.velocity = (0.0, 0.0)

def Draw(deltaTime):
    if Globals.livesLeft <= 0:
        return

    drawPosition = Vector2(playerBody.position.x, Globals.WINDOW_HEIGHT - playerBody.position.y)
    texture = walkingAnimation.GetNextSprite(deltaTime) if abs(playerBody.velocity.x) > 25 else idleAnimation.GetNextSprite(deltaTime)

    # source rectangle (full texture)
    src = Rectangle(0, 0, texture.width, texture.height)

    # destination rectangle
    destWidth = texture.width * renderScale
    destHeight = texture.height * renderScale
    destX = drawPosition.x
    destY = drawPosition.y
    dest = Rectangle(destX, destY, destWidth, destHeight)

    # origin (center of rectangle)
    origin = Vector2(destWidth / 2, destHeight / 2)

    # Flip the sprite if the player is moving left
    if lastDirection < 0:
        src.width = -texture.width

    # rotation = 0
    draw_texture_pro(texture, src, dest, origin, 0.0, WHITE)
