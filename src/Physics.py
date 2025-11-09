import pymunk
import time

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
    last_time = time.time()

    while True:
        current_time = time.time()
        updateDelta = current_time - last_time

        # Update the physics simulation when needed
        if updateDelta >= physicsDelta:
            last_time = current_time
            physWorld.step(physicsDelta)

        # Sleep when a physics update isn't needed, this reduces CPU usage and allows for higher framerates
        else:
            time.sleep(physicsDelta - updateDelta)
