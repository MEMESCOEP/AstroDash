import pymunk

GRAVITY = [0, -981]
PhysWorld = None
BodiesInScene = 0


def InitPhysics():
    print("[INFO:PHYS] >> Initializing pymunk physics engine...")
    print("[INFO:PHYS] >> Initializing physics space...")
    print(f" ╰───╼ Physics space gravity is {GRAVITY[0]} units/sec on the X axis, and {GRAVITY[1]} units/sec on the Y axis\n\r")
    PhysWorld = pymunk.Space()
    PhysWorld.gravity = GRAVITY

    print("[INFO:PHYS] >> Physics space initialized")
