from Globals import *
from pyray import *
from enum import Enum
import Player
import pymunk
import math
import time
import gc

# Values are: (friction, elasticity, density)
class MaterialTypes(Enum):
    CONCRETE_WET = (0.30, 0.2, 2.4)
    CONCRETE_DRY = (1.00, 0.2, 2.4)
    CONCRETE = (0.62, 0.2, 2.4)
    GLASS = (0.94, 0.9, 2.5)
    METAL = (0.50, 0.1, 7.8)
    STEEL = (0.80, 0.15, 7.85)
    WOOD = (0.40, 0.3, 0.7)
    ICE = (0.03, 0.01, 0.92)

class CollisionLayers(Enum):
    DEFAULT: int = 0
    GROUND: int = 2
    WALL: int = 1

PHYSICS_ITERATIONS = 5
PHYSICS_THREADS = 2
PHYSICS_FPS = 120
GRAVITY = -490.5 # Half of earth's gravity, unit is pixels
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

    assert PHYSICS_ITERATIONS > 0, "Physics iterations must be at least 1"
    assert PHYSICS_THREADS > 0, "Physics threads must be at least 1"

    print(f"[INFO:PHYS] >> Initializing physics space...")
    print(f" ├───╼ Physics space gravity is {GRAVITY} u/s")
    print(f" ├───╼ Physics simulation will do {PHYSICS_ITERATIONS} iterations")
    print(f" ╰───╼ Physics simulation will use {PHYSICS_THREADS} thread(s)\n\r")
    physWorld = pymunk.Space(threaded=(PHYSICS_THREADS > 1))
    physWorld.iterations = PHYSICS_ITERATIONS
    physWorld.threads = PHYSICS_THREADS
    physWorld.gravity = [0, GRAVITY]

    print("[INFO:PHYS] >> Physics space initialized")

# Returns the actual body and its index in the physics world
def CreatePhysicsBody(posX, posY, width, height, material, mass=None, friction=None, density=None, elasticity=None, collisionType=CollisionLayers.DEFAULT.value, staticBody=False, instantAdd=False):
    newBody = pymunk.Body(body_type=pymunk.Body.STATIC if staticBody == True else pymunk.Body.DYNAMIC)
    newBody.position = posX, posY
    bodyPoly = pymunk.Poly.create_box(newBody, size=(width, height))

    # Use the material properties with overrides
    materialFriction, materialElasticity, materialDensity = material.value
    bodyPoly.collision_type = collisionType
    bodyPoly.elasticity = elasticity if elasticity is not None else materialElasticity
    bodyPoly.friction = friction if friction is not None else materialFriction
    bodyPoly.density = density if density is not None else materialDensity

    # Optional mass override
    # NOTE: This must happen after the density assignment because setting the density can overwrite the mass
    if mass is not None:
        bodyPoly.mass = mass

    if instantAdd == True:
        physWorld.add(newBody, bodyPoly)

    else:
        bodiesToAdd.append((newBody, bodyPoly))

    return newBody

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

    if isinstance(bodyShape, Segment) == False:
        for vertex in bodyShape.get_vertices():
            rotatedVertex = vertex.rotated(physBody.angle)

            # Translate to the body's position
            worldPosition = rotatedVertex + physBody.position
            worldSpaceVertices.append(worldPosition)

    return worldSpaceVertices

def RemoveBody(body):
    physWorld.remove(body, *body.shapes)

def DrawBodies():
    if modifyingBodies:
        return

    bodiesTuple = tuple(physWorld.bodies)

    if len(bodiesTuple) <= 0:
        return

    crossSize = 4.0
    rl_begin(RL_LINES)

    for body in bodiesTuple:
        # Make sure the body exists and has a shape before we try to draw it
        if body.space is None:
            continue

        shapes = list(body.shapes)

        if not shapes:
            continue

        # Ignore bodies that won't be visible
        if body.position.x // 2 > (WINDOW_WIDTH // 2) + Player.playerBody.position.x:
            continue

        if body.position.x * 2 < Player.playerBody.position.x - (WINDOW_WIDTH // 2):
            continue

        # Draw a cross to mark the center of the body
        rl_color4ub(255, 255, 255, 255)
        cx, cy = body.position.x, WINDOW_HEIGHT - body.position.y
        rl_vertex2f(cx - crossSize, cy)
        rl_vertex2f(cx + crossSize, cy)
        rl_vertex2f(cx, cy - crossSize)
        rl_vertex2f(cx, cy + crossSize)

        # Draw every shape that's attached to the body
        for shape in shapes:
            if isinstance(shape, pymunk.Segment) == True:
                a = shape.a
                b = shape.b

                # Rotate and translate the segment's local transform into world space, using the body's transform
                cos_r = math.cos(body.angle)
                sin_r = math.sin(body.angle)

                ax = a.x * cos_r - a.y * sin_r + body.position.x
                ay = a.x * sin_r + a.y * cos_r + body.position.y
                bx = b.x * cos_r - b.y * sin_r + body.position.x
                by = b.x * sin_r + b.y * cos_r + body.position.y

                # Flip the y axis for Raylib coordinates
                ay = WINDOW_HEIGHT - ay
                by = WINDOW_HEIGHT - by

                # Draw the sensor line
                rl_color4ub(0, 255, 0, 255)
                rl_vertex2f(ax, ay)
                rl_vertex2f(bx, by)

            else:
                rl_color4ub(ORANGE[0], ORANGE[1], ORANGE[2], ORANGE[3])
                verts = shape.get_vertices()

                # Compute half-width and half-height from vertices
                min_x = min(v.x for v in verts)
                max_x = max(v.x for v in verts)
                min_y = min(v.y for v in verts)
                max_y = max(v.y for v in verts)
                hw = (max_x - min_x) / 2
                hh = (max_y - min_y) / 2

                # Unroll the box corners in local space
                x0, y0 = -hw, -hh
                x1, y1 = hw, -hh
                x2, y2 = hw, hh
                x3, y3 = -hw, hh

                cos_r = math.cos(body.angle)
                sin_r = math.sin(body.angle)

                # Rotate and translate each corner to convert from local space to world space
                rx0 = x0 * cos_r - y0 * sin_r + body.position.x
                ry0 = x0 * sin_r + y0 * cos_r + body.position.y
                rx1 = x1 * cos_r - y1 * sin_r + body.position.x
                ry1 = x1 * sin_r + y1 * cos_r + body.position.y
                rx2 = x2 * cos_r - y2 * sin_r + body.position.x
                ry2 = x2 * sin_r + y2 * cos_r + body.position.y
                rx3 = x3 * cos_r - y3 * sin_r + body.position.x
                ry3 = x3 * sin_r + y3 * cos_r + body.position.y

                # Flip the Y coordinate to convert to raylib coords
                ry0 = WINDOW_HEIGHT - ry0
                ry1 = WINDOW_HEIGHT - ry1
                ry2 = WINDOW_HEIGHT - ry2
                ry3 = WINDOW_HEIGHT - ry3

                # Draw the box edges
                rl_vertex2f(rx0, ry0)
                rl_vertex2f(rx1, ry1)
                rl_vertex2f(rx1, ry1)
                rl_vertex2f(rx2, ry2)
                rl_vertex2f(rx2, ry2)
                rl_vertex2f(rx3, ry3)
                rl_vertex2f(rx3, ry3)
                rl_vertex2f(rx0, ry0)

    rl_end()

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
