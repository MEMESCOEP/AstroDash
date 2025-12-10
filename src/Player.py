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

def init():
    global playerBody

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

def movement(delta):
    vx, vy = playerBody.velocity

    if Globals.livesLeft > 0:
        moveRight = pyray.is_key_down(PLAYER_RIGHT_KEY) and wallRight == False
        moveLeft = pyray.is_key_down(PLAYER_LEFT_KEY) and wallLeft == False

        if moveRight == True and moveLeft == False:
            vx = moveSpeed

        elif moveRight == False and moveLeft == True:
            vx = -moveSpeed

        else:
            vx = Globals.Lerp(vx, 0, 10 * delta)

        if grounded == True and pyray.is_key_pressed(pyray.KeyboardKey.KEY_SPACE):
                vy = jumpForce

    if playerBody.position.x < PLAYER_WIDTH:
        vx = max(vx, 0)

    playerBody.velocity = (vx, vy)
    playerBody.moment = float('inf') # Stops body rotation

def health():
    if playerBody.position.y < -PLAYER_HEIGHT:
        Globals.livesLeft = 0
        playerBody.velocity = (0.0, 0.0)

# The player object is currently set as a circle with the position of player_position and a radius of 50, just to be clear
