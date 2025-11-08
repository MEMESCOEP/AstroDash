import pymunk

GRAVITY = [0, -981]
PHYSICS_FPS = 120
physicsDebugDraw = False
physWorld = None
BodiesInScene = 0


def InitPhysics():
    global physWorld
    print("[INFO:PHYS] >> Initializing pymunk physics engine...")
    print("[INFO:PHYS] >> Initializing physics space...")
    print(f" ╰───╼ Physics space gravity is {GRAVITY[0]} units/sec on the X axis, and {GRAVITY[1]} units/sec on the Y axis\n\r")
    physWorld = pymunk.Space()
    physWorld.gravity = GRAVITY

    print("[INFO:PHYS] >> Physics space initialized")

def PhysicsStep():
    physicsDelta = 1.0 / PHYSICS_FPS

    while True:
        physWorld.step(physicsDelta)
