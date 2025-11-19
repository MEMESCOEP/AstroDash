from Globals import *
from pyray import *
from enum import Enum
import pymunk
import math
import time
import gc

class PhysicsBodyShapes(Enum):
    BOX = 1
    SPHERE = 2

GRAVITY = [0, -490.5] # Half of earth's gravity
PHYSICS_ITERATIONS = 5
PHYSICS_THREADS = 2
PHYSICS_FPS = 120
bodiesToRemove = []
bodiesToAdd = []
physicsDebugDraw = False
modifyingBodies = False
worldIsUpdating = False
physSimEnabled = True
physicsSimTimeMS = 0.0
physWorld = None

def InitPhysics():
    global physWorld

    print("[INFO:PHYS] >> Initializing pymunk physics engine...")
    print(f"[INFO:PHYS] >> Initializing physics space ({PHYSICS_THREADS} threads, {PHYSICS_ITERATIONS} iterations)...")
    print(f" ╰───╼ Physics space gravity is {GRAVITY[0]} units/sec on the X axis, and {GRAVITY[1]} units/sec on the Y axis\n\r")
    physWorld = pymunk.Space(threaded=True)
    physWorld.iterations = PHYSICS_ITERATIONS
    physWorld.gravity = GRAVITY
    physWorld.threads = PHYSICS_THREADS

    print("[INFO:PHYS] >> Physics space initialized")

def CreatePhysicsBody(posX, posY, width, height, mass, friction=0.5, staticBody=False):
    newBody = pymunk.Body(body_type=pymunk.Body.STATIC if staticBody == True else pymunk.Body.DYNAMIC)
    newBody.position = posX, posY
    bodyPoly = pymunk.Poly.create_box(newBody, size=(width, height))
    bodyPoly.friction = 0.5
    bodyPoly.mass = mass
    bodiesToAdd.append((newBody, bodyPoly))

def GetPhysBodiesInWorld():
    return len(physWorld.bodies)

# Fixes some unholy python shenanigans
def GetPhysicsWorld():
    return physWorld

# Returns the rotated vertices of the body, relative to its position
def GetBodyWorldVertices(physBody, bodyShape=None):
    # Pick the shape if it wasn't provided
    if bodyShape is None:
        # Get the first Poly shape of the body
        poly_shapes = [s for s in physBody.shapes if isinstance(s, pymunk.Poly)]

        if not poly_shapes:
            return []

        bodyShape = poly_shapes[0]

    # Convert the vertices to world space using the body's angle and position
    worldSpaceVertices = []

    for vertex in bodyShape.get_vertices():
        rotatedVertex = vertex.rotated(physBody.angle)

        # Translate to the body's position
        worldPosition = rotatedVertex + physBody.position
        worldSpaceVertices.append(worldPosition)

    return worldSpaceVertices

def IsBodyVisible(physBody):
    if not physBody.shapes:
        return False
    for shape in physBody.shapes:
        bb = shape.bb
        if not (bb.right < 0 or bb.left > WINDOW_WIDTH or bb.top < 0 or bb.bottom > WINDOW_HEIGHT):
            return True  # At least one shape is still visible
    return False  # All shapes are off-screen

def RemoveBody(body):
    physWorld.remove(body, *body.shapes)

def DrawBodies():
    if modifyingBodies:
        return

    rl_begin(RL_LINES)
    rl_color4ub(ORANGE[0], ORANGE[1], ORANGE[2], ORANGE[3])

    for body in tuple(physWorld.bodies):
        # draw cross at center
        cx, cy = body.position.x, WINDOW_HEIGHT - body.position.y
        s = 3.0
        rl_vertex2f(cx - s, cy)
        rl_vertex2f(cx + s, cy)
        rl_vertex2f(cx, cy - s)
        rl_vertex2f(cx, cy + s)

        # get first shape
        shape = next(iter(body.shapes))
        verts = shape.get_vertices()  # list of Vec2d in local coords

        # compute half-width and half-height from vertices
        min_x = min(v.x for v in verts)
        max_x = max(v.x for v in verts)
        min_y = min(v.y for v in verts)
        max_y = max(v.y for v in verts)
        hw = (max_x - min_x) / 2
        hh = (max_y - min_y) / 2

        # unrolled box corners in local space
        x0, y0 = -hw, -hh
        x1, y1 = hw, -hh
        x2, y2 = hw, hh
        x3, y3 = -hw, hh

        cos_r = math.cos(body.angle)
        sin_r = math.sin(body.angle)

        # rotate and translate each corner
        rx0 = x0 * cos_r - y0 * sin_r + body.position.x
        ry0 = x0 * sin_r + y0 * cos_r + body.position.y
        rx1 = x1 * cos_r - y1 * sin_r + body.position.x
        ry1 = x1 * sin_r + y1 * cos_r + body.position.y
        rx2 = x2 * cos_r - y2 * sin_r + body.position.x
        ry2 = x2 * sin_r + y2 * cos_r + body.position.y
        rx3 = x3 * cos_r - y3 * sin_r + body.position.x
        ry3 = x3 * sin_r + y3 * cos_r + body.position.y

        # flip Y for screen coords
        ry0 = WINDOW_HEIGHT - ry0
        ry1 = WINDOW_HEIGHT - ry1
        ry2 = WINDOW_HEIGHT - ry2
        ry3 = WINDOW_HEIGHT - ry3

        # draw box edges
        rl_vertex2f(rx0, ry0)
        rl_vertex2f(rx1, ry1)
        rl_vertex2f(rx1, ry1)
        rl_vertex2f(rx2, ry2)
        rl_vertex2f(rx2, ry2)
        rl_vertex2f(rx3, ry3)
        rl_vertex2f(rx3, ry3)
        rl_vertex2f(rx0, ry0)

    rl_end()

def BodyRemovalThread():
    while True:
        time.sleep(1)

        if modifyingBodies == True:
            continue

        bodies = tuple(physWorld.bodies)
        for body in bodies:
            if not IsBodyVisible(body):
                bodiesToRemove.append(body)

def PhysicsStep():
    global worldIsUpdating, physicsSimTimeMS
    physicsDelta = 1.0 / PHYSICS_FPS
    last_time = time.time()

    while True:
        bodies_to_remove = []
        current_time = time.time()
        updateDelta = current_time - last_time

        # Update the physics simulation when needed
        if updateDelta >= physicsDelta and physSimEnabled == True:
            simStartTime = time.perf_counter()
            worldIsUpdating = True
            last_time = current_time
            physWorld.step(physicsDelta)
            worldIsUpdating = False

            for body in bodiesToRemove:
                modifyingBodies = True
                physWorld.remove(body, *body.shapes)

            for body, shape in bodiesToAdd:
                modifyingBodies = True
                physWorld.add(body, shape)


            if len(bodiesToRemove) > 0 or len(bodiesToAdd) > 0:
                modifyingBodies = True
                bodiesToRemove.clear()
                bodiesToAdd.clear()
                gc.collect()

            else:
                modifyingBodies = False

            physicsSimTimeMS = (time.perf_counter() - simStartTime) * 1000

        # Sleep when a physics update isn't needed, this reduces CPU usage and allows for higher framerates
        else:
            time.sleep(max(physicsDelta - updateDelta, 0.001))
