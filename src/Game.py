from DebugDefinitions import *
from pyray import *
from Meteor import Meteor
import AssetManager
import MessageBox
import threading
import traceback
import platform
import Globals
import Physics
import Player
import pymunk
import psutil
import random
import time
import sys
import gc
import os

STAR_COLOR = Color(255, 244, 243, 255)
PLATFORM_SPAWN_AHEAD = 350
heartSprites = []
entities = []
stars = []
tiles = []
camera = Camera2D()
operatingSystemName = platform.system()
currentCursor = MOUSE_CURSOR_ARROW
newCursor = MOUSE_CURSOR_ARROW
windowInitialized = False
audioInitialized = False
initFinished = False
gameStarted = False
lastResourceUsageUpdate = 0
lastScoreUpdate = 0
lastTitleUpdate = 0
currentMonitor = 0
lastStarUpdate = 0
uptime = 0
PID = 0
lastPlatformY = 50
nextPlatformCreateX = 150
lastPlatformWidth = 0
nextSpawnCount = 15
platformTexture = None

# The ANSI escape codes here are to overwrite the text that pyray prints when it loads
try:
    print(f"\033[F\33[2K\r[== {Globals.GAME_NAME} ==]")
    print(f"[INFO:MAIN] >> Running on {operatingSystemName}")
    print(f"[INFO:MAIN] >> Using Raylib {RAYLIB_VERSION_MAJOR}.{RAYLIB_VERSION_MINOR}.{RAYLIB_VERSION_PATCH}")

    # Get OpenGL context information from the graphics driver
    oglVersion = rl_get_version()

    if oglVersion > 0 and oglVersion < 7:
        print(f"[INFO:MAIN] >> using OpenGL {Globals.GL_VERSION_MAP.get(oglVersion)}")

    else:
        print(f"[WARN:MAIN] >> Graphics driver reported unknown RlGl OpenGL version \"{oglVersion}\" (could be valid, just not defined in Raylib)")

    print("[INFO:MAIN] >> Getting process PID...")
    PID = os.getpid()

    print(f" ╰───╼ PID is {PID}\n\n[INFO:MAIN] >> Making psutil process...")
    currentProcess = psutil.Process(PID)

    # Parse any CMD args
    argCount = len(sys.argv) - 1

    if argCount > 0:
        print(f"[INFO:MAIN] >> Parsing {len(sys.argv) - 1} CMD arg(s)...")
        skipNextArg = False
        argIndex = 0

        for arg in sys.argv[1:]:
            if skipNextArg == True:
                skipNextArg = False
                continue

            argIndex += 1

            if argIndex > 1:
                print("\033[A\r ├")

            match arg:
                case "--Fullscreen":
                    print(" ╰───╼ Fullscreen mode will be enabled")
                    Globals.fullscreenMode = True

                case "--MonitorIndex":
                    assert (argIndex + 1) < (len(sys.argv)), "No parameter specified for monitor index!"
                    assert sys.argv[argIndex + 1].isnumeric(), "Parameter specified for monitor index must be an integer!"
                    currentMonitor = int(sys.argv[argIndex + 1])
                    skipNextArg = True
                    argIndex += 1
                    print(f" ╰───╼ Monitor {currentMonitor} will be used")

                case "--No-VSync":
                    print(" ╰───╼ VSync will be disabled")
                    Globals.enableVSync = False

                case "--Debug":
                    print(" ╰───╼ Debug mode will be enabled")
                    Globals.enableDebug = True

                case "--No-Load-Errors":
                    print(" ╰───╼ No errors will be shown if assets fail to load...")
                    AssetManager.ShowLoadErrors = False


                case _:
                    print(f" ╰───╼ Invalid CMD arg \"{arg}\"")

        print()

    else:
        print("[INFO:MAIN] >> No CMD args to parse.")

    # Set raylib's logging level so it doesn't spam the console
    print("[INFO:MAIN] >> Setting raylib's logging level...")
    set_trace_log_level(LOG_ERROR | LOG_FATAL)

    # Initialize the game window
    print("[INFO:MAIN] >> Setting game window init properties...")
    if Globals.enableVSync == True:
        print(" ╰───╼ Enabling VSync...")
        set_window_state(FLAG_VSYNC_HINT)
        set_target_fps(0)

    else:
        print(" ╰───╼ Disabling VSync...")
        clear_window_state(FLAG_VSYNC_HINT)

    print(f"\n[INFO:MAIN] >> Creating game window ({WINDOW_WIDTH}x{WINDOW_HEIGHT})...")
    init_window(Globals.WINDOW_WIDTH, Globals.WINDOW_HEIGHT, Globals.GAME_NAME)
    windowInitialized = True

    print("[INFO:MAIN] >> Setting game window post-init properties...")
    # If fullscreen is enabled, update the window width and get_render_height
    # NOTE: This can only be done after the raylib window opens AND before fullscreen is enabled, which is why it happens here
    if Globals.fullscreenMode == True:
        Globals.WINDOW_WIDTH = get_monitor_width(currentMonitor)
        Globals.WINDOW_HEIGHT = get_monitor_height(currentMonitor)
        debugWindowPos = Vector2(Globals.WINDOW_WIDTH - DEBUG_WINDOW_SIZE[0] - 16, 16)
        toggle_fullscreen()

    # Display a loading splash screen
    begin_drawing()
    clear_background(BLACK)
    draw_text("Loading...", Globals.WINDOW_WIDTH - measure_text("Loading...", 20) - 8, Globals.WINDOW_HEIGHT - 28, 20, RAYWHITE)
    end_drawing()

    print("[INFO:MAIN] >> Getting current monitor...")
    monitorIndex = get_current_monitor()

    if monitorIndex != currentMonitor:
        set_window_monitor(currentMonitor)

    print(f" ╰───╼ Current monitor is \"{get_monitor_name(currentMonitor)}\" (index={currentMonitor})...")

    # Initialize audio device(s)
    print("\n[INFO:MAIN] >> Initializing audio device(s)...")
    init_audio_device()

    # Wait up to 5 seconds for the audio device to be ready
    waitTime = 0
    while not is_audio_device_ready():
        waitTime += 1

        if waitTime > 5000:
            raise Exception("Audio device did not become ready within 5 seconds")

        time.sleep(0.001)

    audioInitialized = True

    # Initialize the physics engine
    Physics.InitPhysics()
    threading.Thread(target=Physics.PhysicsStep, daemon=True).start()

    # Create physics bodies
    Physics.CreatePhysicsBody(125, 20, 250, 30, Physics.MaterialTypes.CONCRETE_DRY, staticBody=True, collisionType=Physics.CollisionLayers.GROUND.value)
    Player.Init()

    # Read the stats file to get the high score
    if os.path.exists(Globals.STATS_FILE) == True:
        print(f"[INFO:MAIN] >> Reading game stats file \"{Globals.STATS_FILE}\"...")
        try:
            with open(Globals.STATS_FILE, 'r') as StatsFile:
                for line in StatsFile.readlines():
                    if line.startswith("HI=") == True:
                        Globals.highScore = int(line[3:])

        except Exception as EX:
            print(f"[ERROR:MAIN] >> Failed to read \"{Globals.STATS_FILE}\": {EX}")

    else:
        print(f"[INFO:MAIN] >> Game stats file \"{Globals.STATS_FILE}\" doesn't exist")

    # Disable escape to exit
    print("[INFO:MAIN] >> Disabling escape to exit...")
    set_exit_key(KEY_NULL)

    # Load assets
    print("[INFO:MAIN] >> Loading textures...")
    heartSprites = [AssetManager.LoadTexture("Assets/Icons/HeartFull.png"), AssetManager.LoadTexture("Assets/Icons/HeartEmpty.png")]
    platformTexture = AssetManager.LoadTexture("Assets/Icons/scifi_floortile.jpg")

    # Place the stars in the background
    print(f"[INFO:MAIN] >> Placing {Globals.STAR_COUNT} star(s)...")
    for i in range(Globals.STAR_COUNT):
        starVector = Vector2(random.randint(2, Globals.WINDOW_WIDTH), random.randint(2, Globals.WINDOW_HEIGHT))
        starAngle = random.uniform(0, 360)
        starScale = random.uniform(Globals.STAR_SCALE_RANGE[0], Globals.STAR_SCALE_RANGE[1])
        stars.append([starVector, starScale, starAngle])

    print(f"[INFO:MAIN] >> Placing 10 meteor(s)...")
    for i in range(5):
        meteor = Meteor(Globals.WINDOW_WIDTH + random.randint(10, 50), random.randint(10, 300), random.randint(100, 200), random.randint(75, 125))
        entities.append(meteor)

    # Configure the camera
    print("[INFO:MAIN] >> Configuring the camera...")
    camera.offset = Vector2(0, 0)
    camera.target = Vector2(0, 0)
    camera.rotation = 0.0
    camera.zoom = 1.0

    # Call the garbage collector
    print("[INFO:MAIN] >> Running garbage collector...")
    collectedObjects = gc.collect()
    print(f" ╰───╼ Collected {collectedObjects} objects\n")
    initFinished = True

except Exception as EX:
    print(f"[ERROR:MAIN] >> Error during init: {EX}")
    traceback.print_exc()
    MessageBox.showMessage(MessageBox.MessageTypes.ERROR, "Error during initialization", f"An error occurred during initialization, see the console for more information.\n\n{EX}")

# Start the game loop
if initFinished == True:

    print("[INFO:MAIN] >> Init finished, starting game loop...")
    try:
        while window_should_close() == False:
            # === USER INTERACTION ===
            # Get user input before drawing the frame
            if is_key_pressed(KEY_ENTER):
                gameStarted = True

            mouseDelta = get_mouse_delta()
            mousePos = get_mouse_position()

            # Toggle debugging by pressing the '`' key
            if is_key_pressed(KEY_GRAVE):
                if draggingWindow == True:
                    draggingWindow = False

                set_mouse_cursor(MOUSE_CURSOR_ARROW)
                newCursor = MOUSE_CURSOR_ARROW
                Globals.enableDebug = not Globals.enableDebug
                print("[INFO:MAIN] >> Debugging is now " + ("enabled" if Globals.enableDebug == True else "disabled"))

            # Toggle physics debug drawing
            if is_key_pressed(KEY_P):
                Physics.physicsDebugDraw = not Physics.physicsDebugDraw

            # Debug window handling
            if Globals.enableDebug == True:
                leftPressed = is_mouse_button_pressed(MOUSE_BUTTON_LEFT)
                rightPressed = is_mouse_button_pressed(MOUSE_BUTTON_RIGHT)
                leftReleased = is_mouse_button_released(MOUSE_BUTTON_LEFT)
                isHoveringTitlebar = Globals.IsPointInsideRect(mousePos, debugWindowPos.x, debugWindowPos.y, DEBUG_WINDOW_SIZE[0], 20)
                hoveringDebugCloseButton = Globals.IsPointInsideRect(mousePos, debugWindowPos.x + DEBUG_WINDOW_CLOSE_X_POS, debugWindowPos.y, 20, 20)

                # Handle window dragging
                if leftPressed == True:
                    if isHoveringTitlebar == True and hoveringDebugCloseButton == False:
                        draggingWindow = True

                # Handle hiding/showing the debug contents
                elif rightPressed == True and isHoveringTitlebar == True and draggingWindow == False and hoveringDebugCloseButton == False:
                    debugContentsHidden = not debugContentsHidden

                elif leftReleased == True:
                    debugWindowPos.x = min(max(5, debugWindowPos.x), WINDOW_WIDTH - DEBUG_WINDOW_SIZE[0] - 5)
                    debugWindowPos.y = min(max(5, debugWindowPos.y), WINDOW_HEIGHT - DEBUG_WINDOW_SIZE[1] - 5)
                    draggingWindow = False

                # Update the debug window's position while it's being dragged
                if draggingWindow == True:
                    debugWindowPos.x += mouseDelta.x
                    debugWindowPos.y += mouseDelta.y

                # Handle window closing
                if leftReleased == True and hoveringDebugCloseButton == True:
                    print("[INFO:MAIN] >> Debugging is now disabled")
                    set_mouse_cursor(MOUSE_CURSOR_ARROW)
                    newCursor = MOUSE_CURSOR_ARROW
                    hoveringDebugCloseButton = False
                    isHoveringTitlebar = False
                    draggingWindow = False
                    Globals.enableDebug = False

                # Set the cursor type
                if draggingWindow == True:
                    newCursor = MOUSE_CURSOR_RESIZE_ALL

                elif hoveringDebugCloseButton == True:
                    newCursor = MOUSE_CURSOR_POINTING_HAND

                elif isHoveringTitlebar == True:
                    newCursor = MOUSE_CURSOR_RESIZE_ALL

                else:
                    newCursor = MOUSE_CURSOR_ARROW

            # Set the cursor when it changes
            if currentCursor != newCursor:
                set_mouse_cursor(newCursor)
                currentCursor = newCursor

            # Update the music streams so they keep playing
            AssetManager.UpdateMusicStreams()

            # Handle player movement and health
            if gameStarted == True:
                Player.Movement(Globals.deltaTime)
                Player.Health()

            # Start the frame
            begin_drawing()
            clear_background(WINDOW_BG_COLOR)



            # === GRAPHICS ===
            # SCREEN SPACE
            # Draw the stars
            for star in stars:
                starSideCount = 3
                starTwinkle = random.randint(1, 250)

                if starTwinkle > 90:
                    starSideCount = 4

                elif starTwinkle == 5:
                    continue

                draw_poly(star[0], starSideCount, star[1], star[2], STAR_COLOR)

            # WORLD SPACE
            begin_mode_2d(camera)

            # Draw meteors
            for meteor in entities:
                meteor.Draw(Globals.deltaTime)

            # Draw the player
            Player.Draw(Globals.deltaTime)

            # Draw physics bodies if physics debugging is enabled
            if Physics.physicsDebugDraw == True:
                Physics.DrawBodies()

            # Draw the platforms
            for body in Physics.physWorld.bodies[1:]:
                for shape in body.shapes:
                    if isinstance(shape, pymunk.Poly):

                        # Get the box size from local (unrotated) vertices
                        local = shape.get_vertices()
                        xs = [v.x for v in local]
                        ys = [v.y for v in local]

                        w = max(xs) - min(xs)
                        h = max(ys) - min(ys)

                        # Convert pymunk Y to raylib Y coordinates
                        rx = body.position.x
                        ry = Globals.WINDOW_HEIGHT - body.position.y

                        # Convert pymunk CCW to raylib CW angles
                        angle_deg = -(body.angle * 57.2958)

                        # Draw the sprite centered on the body
                        draw_texture_pro(
                            platformTexture,
                            Rectangle(0, 0, platformTexture.width, platformTexture.height),
                            Rectangle(rx, ry, w, h),
                            Vector2(w/2, h/2),
                            angle_deg,
                            WHITE
                        )

            end_mode_2d()



            # === USER INTERFACE ===
            # NOTE: UI elements should be drawn last so they always draw on top

            # Draw the lives and scores
            for life in range(Globals.livesLeft):
                draw_texture_ex(heartSprites[0], Vector2((32 * life) - 12, -12), 0.0, 2.0, WHITE)

            for life in range(max(Globals.LIFE_COUNT - Globals.livesLeft, 0)):
                endOfHealthbar = 32 * (Globals.LIFE_COUNT - 1)
                lifeToPixel = (32 * life) + 12
                draw_texture_ex(heartSprites[1], Vector2(endOfHealthbar - lifeToPixel, -12), 0.0, 2.0, WHITE)

            if Globals.livesLeft > 0:
                draw_text(f"SCORE: {Globals.score}", 10, 42, 20, DARKPURPLE)
                draw_text(f"HI: {Globals.highScore}", 10, 62, 20, DARKPURPLE)
                draw_text(f"SCORE: {Globals.score}", 8, 40, 20, MAGENTA)
                draw_text(f"HI: {Globals.highScore}", 8, 60, 20, MAGENTA)

            # Draw a full-window black rectangle when the player dies
            else:
                gameOverTextLen = measure_text("<=== GAME OVER ===>", 40)
                draw_text("<=== GAME OVER ===>", (WINDOW_WIDTH // 2) - (gameOverTextLen // 2) + 2, 72, 40, Color(128, 0, 0, 255))
                draw_text("<=== GAME OVER ===>", (WINDOW_WIDTH // 2) - (gameOverTextLen // 2), 70, 40, RED)
                draw_text(f"{Globals.score} POINTS SCORED", (WINDOW_WIDTH // 2) - (measure_text(f"{Globals.score} POINTS SCORED", 20) // 2), 110, 20, MAGENTA)

                if Globals.score >= Globals.highScore:
                    draw_text("!! NEW HIGH SCORE !!", (WINDOW_WIDTH // 2) - (measure_text("!! NEW HIGH SCORE !!", 20) // 2), 130, 20, MAGENTA)

                else:
                    draw_text(f"HI SCORE IS {Globals.highScore}", (WINDOW_WIDTH // 2) - (measure_text(f"HI SCORE IS {Globals.highScore}", 20) // 2), 130, 20, MAGENTA)

            if gameStarted == False:
                draw_text("<== PRESS ENTER TO PLAY ==>", (WINDOW_WIDTH // 2) - (measure_text("<== PRESS ENTER TO PLAY ==>", 30) // 2), 130, 30, MAGENTA)
                draw_text("A AND D TO MOVE", (WINDOW_WIDTH // 2) - (measure_text("A AND D TO MOVE", 20) // 2), 170, 20, MAGENTA)
                draw_text("SPACE TO JUMP", (WINDOW_WIDTH // 2) - (measure_text("SPACE TO JUMP", 20) // 2), 200, 20, MAGENTA)

            # Draw debugging statistics if debugging is enabled
            if Globals.enableDebug == True:
                # Draw the debug data in the window
                if debugContentsHidden == False:
                    draw_rectangle_lines(int(debugWindowPos.x), int(debugWindowPos.y), DEBUG_WINDOW_SIZE[0], DEBUG_WINDOW_SIZE[1], GRAY)
                    draw_rectangle(int(debugWindowPos.x), int(debugWindowPos.y) + 20, DEBUG_WINDOW_SIZE[0] - 1, DEBUG_WINDOW_SIZE[1] - 21, DEBUG_WINDOW_BG_COLOR)
                    draw_text("=== PERFORMANCE & METRICS ===", int(debugWindowPos.x) + 2, int(debugWindowPos.y) + 22, 10, RAYWHITE)
                    draw_text(f"Uptime: {int(uptime) // 3600:02d}:{(int(uptime) // 60) % 60:02d}:{int(uptime % 60):02d}:{int(uptime * 100) % 100:02d}", int(debugWindowPos.x) + 2, int(debugWindowPos.y) + 32, 10, RAYWHITE)
                    draw_text(f"Frame delta: {Globals.deltaTime*1000:.4f}ms", int(debugWindowPos.x) + 2, int(debugWindowPos.y) + 42, 10, RAYWHITE)
                    draw_text(f"Frames drawn: {Globals.frameCount}", int(debugWindowPos.x) + 2, int(debugWindowPos.y) + 52, 10, RAYWHITE)
                    draw_text(f"Framerate: {Globals.FPS}", int(debugWindowPos.x) + 2, int(debugWindowPos.y) + 62, 10, RAYWHITE)
                    draw_text(f"CPU usage: {cpuUsage:.2f}%", int(debugWindowPos.x) + 2, int(debugWindowPos.y) + 72, 10, RAYWHITE)
                    draw_text(f"MEM usage: {memUsageKB} KB ({memUsageKB / 1024:.2f} MB)", int(debugWindowPos.x) + 2, int(debugWindowPos.y) + 82, 10, RAYWHITE)
                    draw_text("=== WORLD & PHYSICS ===", int(debugWindowPos.x) + 2, int(debugWindowPos.y) + 102, 10, RAYWHITE)
                    draw_text(f"Physics debug draw: {'ON' if Physics.physicsDebugDraw == True else 'OFF'}", int(debugWindowPos.x) + 2, int(debugWindowPos.y) + 112, 10, RAYWHITE)
                    draw_text(f"Physics simulation time: {Physics.physicsSimTimeMS:.3f}ms", int(debugWindowPos.x) + 2, int(debugWindowPos.y) + 122, 10, RAYWHITE)
                    draw_text(f"Player position: ({Player.playerBody.position.x:.3f}, {Player.playerBody.position.y:.3f})", int(debugWindowPos.x) + 2, int(debugWindowPos.y) + 132, 10, RAYWHITE)
                    draw_text(f"Player velocity: ({Player.playerBody.velocity.x:.3f}, {Player.playerBody.velocity.y:.3f})", int(debugWindowPos.x) + 2, int(debugWindowPos.y) + 142, 10, RAYWHITE)
                    draw_text(f"Physics bodies in scene: {Physics.GetPhysBodiesInWorld()}", int(debugWindowPos.x) + 2, int(debugWindowPos.y) + 152, 10, RAYWHITE)
                    draw_text(f"Entities in scene: {len(entities)}", int(debugWindowPos.x) + 2, int(debugWindowPos.y) + 162, 10, RAYWHITE)
                    draw_text(f"Tiles in scene: {len(tiles)}", int(debugWindowPos.x) + 2, int(debugWindowPos.y) + 172, 10, RAYWHITE)

                # Draw the debug window's titlebar
                draw_rectangle_lines(int(debugWindowPos.x), int(debugWindowPos.y), DEBUG_WINDOW_SIZE[0], 20, LIGHTGRAY)
                draw_rectangle_gradient_h(int(debugWindowPos.x), int(debugWindowPos.y), DEBUG_WINDOW_SIZE[0] - 1, 19, DEBUG_TITLEBAR_BEGIN_GRADIENT_COLOR, DEBUG_TITLEBAR_END_GRADIENT_COLOR)
                draw_rectangle_lines(int(debugWindowPos.x) + DEBUG_WINDOW_CLOSE_X_POS, int(debugWindowPos.y) + 2, 18, 16, LIGHTGRAY)
                draw_rectangle(int(debugWindowPos.x) + DEBUG_WINDOW_CLOSE_X_POS, int(debugWindowPos.y) + 2, 17, 15, MAROON if hoveringDebugCloseButton == True else DEBUG_CLOSE_BUTTON_COLOR)
                draw_text("X", int(debugWindowPos.x) + DEBUG_WINDOW_CLOSE_X_POS + 4, int(debugWindowPos.y) + 4, 13, RAYWHITE)
                draw_text("Debug" if debugContentsHidden == False else "Debug (hidden)", int(debugWindowPos.x) + 8, int(debugWindowPos.y) + 3, 15, LIGHTGRAY)

            # End the frame
            end_drawing()



            # === STATE UPDATES ===
            # Move the world left and right based on the player position
            px = Player.playerBody.position.x
            SCROLL_TRIGGERS = (100, Globals.WINDOW_WIDTH // 2)  # screen-space threshold from the center

            if px > camera.target.x + SCROLL_TRIGGERS[1]:
                camera.target.x = px - SCROLL_TRIGGERS[1]

            if camera.target.x > 0 and px < camera.target.x + SCROLL_TRIGGERS[0]:
                camera.target.x = px - SCROLL_TRIGGERS[0]

            camera.target.x = max(camera.target.x, 0)

            # Move the meteors
            if gameStarted == True:
                for meteor in entities:
                    meteor.Move(Globals.deltaTime, camera.target.x, Player.playerBody.position)

            # Spawn 5 new meteors for every 15 new platforms
            if Physics.GetPhysBodiesInWorld() >= nextSpawnCount:
                nextSpawnCount += 15

                for i in range(5):
                    meteor = Meteor(0, 0, random.randint(100, 200), random.randint(75, 125))
                    entities.append(meteor)

            # Spawn new platforms when needed
            while nextPlatformCreateX < Player.playerBody.position.x + PLATFORM_SPAWN_AHEAD:
                platformHeight = random.randint(10, 50)
                platformWidth = random.randint(80, 750)
                nextPlatformCreateX += (lastPlatformWidth // 2) + random.randint(100, 150) + (platformWidth // 2)

                Physics.CreatePhysicsBody(
                    nextPlatformCreateX,
                    platformHeight // 2,
                    platformWidth,
                    platformHeight,
                    Physics.MaterialTypes.CONCRETE_DRY,
                    staticBody=True,
                    collisionType=Physics.CollisionLayers.GROUND.value
                )

                lastPlatformWidth = platformWidth

            # Update the frame count, delta time, game uptime, and FPS values
            Globals.frameCount += 1
            Globals.deltaTime = get_frame_time()
            Globals.FPS = get_fps()
            uptime += Globals.deltaTime

            # Move stars and check if any of them are out of bounds
            if uptime >= lastStarUpdate:
                lastStarUpdate = uptime + (Globals.STAR_UPDATE_INTERVAL_MS / 1000)

                for star in stars:
                    star[0].x -= 1
                    star[2] += random.uniform(-1, 2)

                    if star[0].x < -8:
                        star[0].x = Globals.WINDOW_WIDTH + random.randint(8, 64)
                        star[0].y = random.randint(0, Globals.WINDOW_HEIGHT)
                        star[1] = random.uniform(Globals.STAR_SCALE_RANGE[0], Globals.STAR_SCALE_RANGE[1])
                        star[2] = random.uniform(0, 360)

            # Update the score and high score when ready
            if uptime >= lastScoreUpdate and gameStarted == True:
                lastScoreUpdate = uptime + (Globals.SCORE_INCREASE_INTERVAL_MS / 1000)

                if Globals.livesLeft > 0:
                    Globals.score += 1

                    if Globals.score > Globals.highScore:
                        Globals.highScore = Globals.score

            # Update the title when ready
            if uptime >= lastTitleUpdate:
                lastTitleUpdate = uptime + (Globals.TITLE_UPDATE_INTERVAL_MS / 1000)
                set_window_title(f"{Globals.GAME_NAME} | {Globals.WINDOW_WIDTH}x{Globals.WINDOW_HEIGHT} | {Globals.FPS} FPS")

            # Get this program's resource usage when ready, and debugging is enabled
            if Globals.enableDebug == True and uptime >= lastResourceUsageUpdate:
                lastResourceUsageUpdate = uptime + (Globals.RESOURCE_USAGE_UPDATE_INTERVAL_MS / 1000)
                cpuUsage = currentProcess.cpu_percent(interval=None) / psutil.cpu_count()
                memUsageKB = currentProcess.memory_info().rss / 1024

    except Exception as EX:
        print(f"[ERROR:MAIN] >> Error in window loop: {EX}")
        traceback.print_exc()
        MessageBox.showMessage(MessageBox.MessageTypes.ERROR, "Error in window loop", f"An error occurred in the window loop, see the console for more information.\n\n{EX}")

# Clean up
print("[INFO:MAIN] >> Game loop exited, cleaning up...")

# Unload assets
AssetManager.UnloadAllAssets()

# Close audio device contexts
if audioInitialized == True:
    print("[INFO:MAIN] >> Closing audio device(s)...")
    close_audio_device()

# Close the game window
if windowInitialized == True:
    print("[INFO:MAIN] >> Closing game window...")
    close_window()

# Write the user's high score to a file
if initFinished == True:
    print(f"[INFO:MAIN] >> Saving game stats to \"{Globals.STATS_FILE}\"...")
    try:
        with open(Globals.STATS_FILE, 'w') as StatsFile:
            StatsFile.write(f"HI={Globals.highScore}\n")

    except Exception as EX:
        print(f"[ERROR:MAIN] >> Failed to write to \"{Globals.STATS_FILE}\": {EX}")
        traceback.print_exc()
        MessageBox.showMessage(MessageBox.MessageTypes.ERROR, "Failed to save high score", f"An error occurred while saving your high score, see the console for more information.\n\n{EX}")

# Call the garbage collector
print("[INFO:MAIN] >> Running final garbage collection...")
collectedObjects = gc.collect()
print(f" ╰───╼ Collected {collectedObjects} objects\n")

print("[INFO:MAIN] >> Exiting...")
