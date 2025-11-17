from Globals import *
from pyray import draw_circle_lines, draw_line, ORANGE
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
worldIsUpdating = False
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
    for body in physWorld.bodies:
        bodyVertices = GetBodyWorldVertices(body)
        vertexCount = len(bodyVertices)

        draw_circle_lines(int(body.position.x), int(WINDOW_HEIGHT - body.position.y), 3, ORANGE)
        for i in range(vertexCount):
            startVertex = bodyVertices[i - 1]
            endVertex = bodyVertices[i]
            draw_circle_lines(int(endVertex.x), int(WINDOW_HEIGHT - endVertex.y), 2, ORANGE)
            draw_line(int(startVertex.x), int(WINDOW_HEIGHT - startVertex.y), int(endVertex.x), int(WINDOW_HEIGHT - endVertex.y), ORANGE)

def BodyRemovalThread():
    while True:
        for body in physWorld.bodies:
            if not IsBodyVisible(body):
                bodiesToRemove.append(body)

        time.sleep(0.05)

def PhysicsStep():
    global worldIsUpdating
    physicsDelta = 1.0 / PHYSICS_FPS
    last_time = time.time()

    while True:
        bodies_to_remove = []
        current_time = time.time()
        updateDelta = current_time - last_time

        # Update the physics simulation when needed
        if updateDelta >= physicsDelta:
            worldIsUpdating = True
            last_time = current_time
            physWorld.step(physicsDelta)
            worldIsUpdating = False

            for body in bodiesToRemove:
                physWorld.remove(body, *body.shapes)

            for body, shape in bodiesToAdd:
                physWorld.add(body, shape)


            if len(bodiesToRemove) > 0 or len(bodiesToAdd) > 0:
                bodiesToRemove.clear()
                bodiesToAdd.clear()
                #gc.collect()

        # Sleep when a physics update isn't needed, this reduces CPU usage and allows for higher framerates
        else:
            time.sleep(physicsDelta - updateDelta)
