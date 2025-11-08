from DebugDefinitions import *
from WorldState import *
from Globals import *
from Physics import *
from Player import *
from pyray import *
import threading
import platform
import psutil
import sys
import gc
import os

heartSprites = []
operatingSystemName = platform.system()
currentCursor = MOUSE_CURSOR_ARROW
newCursor = MOUSE_CURSOR_ARROW
lastResourceUsageUpdate = 0
lastScoreUpdate = 0
lastTitleUpdate = 0
uptime = 0
PID = 0

# The ANSI escape codes here are to overwrite the text that pyray prints when it loads
print(f"\033[F\33[2K\r[== {GAME_NAME} ==]")
print(f"[INFO:MAIN] >> Running on {operatingSystemName}")
print(f"[INFO:MAIN] >> Using Raylib {RAYLIB_VERSION_MAJOR}.{RAYLIB_VERSION_MINOR}.{RAYLIB_VERSION_PATCH}")

# Get OpenGL context information from the graphics driver
oglVersion = rl_get_version()

if oglVersion > 0 and oglVersion < 7:
    print(f"[INFO:MAIN] >> using OpenGL {GL_VERSION_MAP.get(oglVersion)}")

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
    argIndex = 0

    for arg in sys.argv[1:]:
        argIndex += 1

        if argIndex > 1:
            print("\033[A\r ├")

        match arg:
            case "--Fullscreen":
                print(" ╰───╼ Fullscreen mode will be enabled")
                fullscreenMode = True

            case "--No-VSync":
                print(" ╰───╼ VSync will be disabled")
                enableVSync = False

            case "--Debug":
                print(" ╰───╼ Debug mode will be enabled...")
                enableDebug = True

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
if enableVSync == True:
    print(" ╰───╼ Enabling VSync...")
    set_window_state(FLAG_VSYNC_HINT)
    set_target_fps(0)

else:
    print(" ╰───╼ Disabling VSync...")
    clear_window_state(FLAG_VSYNC_HINT)

print(f"\n[INFO:MAIN] >> Creating game window ({WINDOW_WIDTH}x{WINDOW_HEIGHT})...")
init_window(WINDOW_WIDTH, WINDOW_HEIGHT, GAME_NAME)

print("[INFO:MAIN] >> Setting game window post-init properties...")
# If fullscreen is enabled, update the window width and get_render_height
# NOTE: This can only be done after the raylib window opens AND before fullscreen is enabled, which is why it happens here
if fullscreenMode == True:
    currentMonitor = get_current_monitor()
    WINDOW_WIDTH = get_monitor_width(currentMonitor)
    WINDOW_HEIGHT = get_monitor_height(currentMonitor)
    debugWindowPos = Vector2(WINDOW_WIDTH - DEBUG_WINDOW_SIZE[0] - 16, 16)
    toggle_fullscreen()

# Display a loading splash screen
begin_drawing()
clear_background(BLACK)
draw_text("Loading...", WINDOW_WIDTH - measure_text("Loading...", 20) - 8, WINDOW_HEIGHT - 28, 20, RAYWHITE)
end_drawing()

# Initialize the physics engine
InitPhysics()

# Read the stats file to get the high score
if os.path.exists(STATS_FILE) == True:
    print(f"[INFO:MAIN] >> Reading game stats file \"{STATS_FILE}\"...")
    try:
        with open(STATS_FILE, 'r') as StatsFile:
            for line in StatsFile.readlines():
                if line.startswith("HI=") == True:
                    highScore = int(line[3:])

    except Exception as EX:
        print(f"[ERROR:MAIN] >> Failed to read \"{STATS_FILE}\": {EX}")

else:
    print(f"[INFO:MAIN] >> Game stats file \"{STATS_FILE}\" doesn't exist")

# Load assets
print("[INFO:MAIN] >> Loading textures...")
heartSprites = [load_texture("Assets/Icons/HeartFull.png"), load_texture("Assets/Icons/HeartEmpty.png")]

# Start threads
threading.Thread(target=PhysicsStep, daemon=True).start()

# Call the garbage collector
print("[INFO:MAIN] >> Running garbage collector...")
collectedObjects = gc.collect()
print(f" ╰───╼ Collected {collectedObjects} objects\n")

# Start the game loop
print("[INFO:MAIN] >> Init finished, starting game loop...")
try:
    while window_should_close() == False:
        # Get user input before begin_drawing
        mouseDelta = get_mouse_delta()
        mousePos = get_mouse_position()

        # Toggle debugging by pressing the '`' key
        if is_key_pressed(KEY_GRAVE):
            if draggingWindow == True:
                draggingWindow = False

            set_mouse_cursor(MOUSE_CURSOR_ARROW)
            newCursor = MOUSE_CURSOR_ARROW
            enableDebug = not enableDebug
            print("[INFO:MAIN] >> Debugging is now " + ("enabled" if enableDebug == True else "disabled"))

        # Toggle physics debug drawing
        if is_key_pressed(KEY_P):
            physicsDebugDraw = not physicsDebugDraw

        # Debug window handling
        if enableDebug == True:
            leftPressed = is_mouse_button_pressed(MOUSE_BUTTON_LEFT)
            rightPressed = is_mouse_button_pressed(MOUSE_BUTTON_RIGHT)
            leftReleased = is_mouse_button_released(MOUSE_BUTTON_LEFT)
            isHoveringTitlebar = IsPointInsideRect(mousePos, debugWindowPos.x, debugWindowPos.y, DEBUG_WINDOW_SIZE[0], 20)
            hoveringDebugCloseButton = IsPointInsideRect(mousePos, debugWindowPos.x + DEBUG_WINDOW_CLOSE_X_POS, debugWindowPos.y, 20, 20)

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
                enableDebug = False

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

        if is_key_pressed(KEY_SPACE):
            if is_key_down(KEY_LEFT_SHIFT):
                if livesLeft < LIFE_COUNT:
                    livesLeft += 1

            else:
                livesLeft -= 1

        # Start the frame
        begin_drawing()
        clear_background(WINDOW_BG_COLOR)

        # === USER INTERFACE ===
        # NOTE: UI elements should be drawn last so they always draw on top

        # Draw debugging statistics if debugging is enabled
        if enableDebug == True:
            # Draw the debug data in the window
            if debugContentsHidden == False:
                draw_rectangle_lines(int(debugWindowPos.x), int(debugWindowPos.y), DEBUG_WINDOW_SIZE[0], DEBUG_WINDOW_SIZE[1], GRAY)
                draw_rectangle(int(debugWindowPos.x), int(debugWindowPos.y) + 20, DEBUG_WINDOW_SIZE[0] - 1, DEBUG_WINDOW_SIZE[1] - 21, DEBUG_WINDOW_BG_COLOR)
                draw_text("=== PERFORMANCE & METRICS ===", int(debugWindowPos.x) + 2, int(debugWindowPos.y) + 22, 10, RAYWHITE)
                draw_text(f"Uptime: {int(uptime) // 3600:02d}:{(int(uptime) // 60) % 60:02d}:{int(uptime % 60):02d}", int(debugWindowPos.x) + 2, int(debugWindowPos.y) + 32, 10, RAYWHITE)
                draw_text(f"Frame delta: {deltaTime*1000:.4f}ms", int(debugWindowPos.x) + 2, int(debugWindowPos.y) + 42, 10, RAYWHITE)
                draw_text(f"Frames drawn: {frameCount}", int(debugWindowPos.x) + 2, int(debugWindowPos.y) + 52, 10, RAYWHITE)
                draw_text(f"Framerate: {FPS}", int(debugWindowPos.x) + 2, int(debugWindowPos.y) + 62, 10, RAYWHITE)
                draw_text(f"CPU usage: {cpuUsage:.2f}%", int(debugWindowPos.x) + 2, int(debugWindowPos.y) + 72, 10, RAYWHITE)
                draw_text(f"MEM usage: {memUsageKB} KB ({memUsageKB / 1024:.2f} MB)", int(debugWindowPos.x) + 2, int(debugWindowPos.y) + 82, 10, RAYWHITE)
                draw_text("=== WORLD & PHYSICS ===", int(debugWindowPos.x) + 2, int(debugWindowPos.y) + 102, 10, RAYWHITE)
                draw_text(f"Physics debug draw: {'ON' if physicsDebugDraw == True else 'OFF'}", int(debugWindowPos.x) + 2, int(debugWindowPos.y) + 112, 10, RAYWHITE)
                draw_text(f"Player position: ({PlayerPosition[0]:.3f}, {PlayerPosition[1]:.3f})", int(debugWindowPos.x) + 2, int(debugWindowPos.y) + 122, 10, RAYWHITE)
                draw_text(f"Physics bodies in scene: {len(Tiles)}", int(debugWindowPos.x) + 2, int(debugWindowPos.y) + 132, 10, RAYWHITE)
                draw_text(f"Entities in scene: {len(Entities)}", int(debugWindowPos.x) + 2, int(debugWindowPos.y) + 142, 10, RAYWHITE)
                draw_text(f"Tiles in scene: {BodiesInScene}", int(debugWindowPos.x) + 2, int(debugWindowPos.y) + 152, 10, RAYWHITE)
                draw_text("=== SYSTEM ===", int(debugWindowPos.x) + 2, int(debugWindowPos.y) + 172, 10, RAYWHITE)
                draw_text(f"Operating system: {operatingSystemName}", int(debugWindowPos.x) + 2, int(debugWindowPos.y) + 182, 10, RAYWHITE)
                draw_text(f"Raylib version: {RAYLIB_VERSION_MAJOR}.{RAYLIB_VERSION_MINOR}.{RAYLIB_VERSION_PATCH}", int(debugWindowPos.x) + 2, int(debugWindowPos.y) + 192, 10, RAYWHITE)

                if oglVersion > 0 and oglVersion < 7:
                    draw_text(f"OpenGL version: {GL_VERSION_MAP.get(oglVersion)}", int(debugWindowPos.x) + 2, int(debugWindowPos.y) + 202, 10, RAYWHITE)

                else:
                    draw_text(f"OpenGL version: {oglVersion} (undefined by RlGl)", int(debugWindowPos.x) + 2, int(debugWindowPos.y) + 202, 10, RAYWHITE)

            # Draw the debug window's titlebar
            draw_rectangle_lines(int(debugWindowPos.x), int(debugWindowPos.y), DEBUG_WINDOW_SIZE[0], 20, LIGHTGRAY)
            draw_rectangle_gradient_h(int(debugWindowPos.x), int(debugWindowPos.y), DEBUG_WINDOW_SIZE[0] - 1, 19, DEBUG_TITLEBAR_BEGIN_GRADIENT_COLOR, DEBUG_TITLEBAR_END_GRADIENT_COLOR)
            draw_rectangle_lines(int(debugWindowPos.x) + DEBUG_WINDOW_CLOSE_X_POS, int(debugWindowPos.y) + 2, 18, 16, LIGHTGRAY)
            draw_rectangle(int(debugWindowPos.x) + DEBUG_WINDOW_CLOSE_X_POS, int(debugWindowPos.y) + 2, 17, 15, MAROON if hoveringDebugCloseButton == True else DEBUG_CLOSE_BUTTON_COLOR)
            draw_text("X", int(debugWindowPos.x) + DEBUG_WINDOW_CLOSE_X_POS + 4, int(debugWindowPos.y) + 4, 13, RAYWHITE)
            draw_text("Debug" if debugContentsHidden == False else "Debug (hidden)", int(debugWindowPos.x) + 8, int(debugWindowPos.y) + 3, 15, LIGHTGRAY)

        # Draw the lives and scores
        #draw_rectangle(0, 0, max(136, measure_text(f"SCORE: {score}", 20) + 16), 86, DEBUG_WINDOW_BG_COLOR)

        for life in range(livesLeft):
            draw_texture_ex(heartSprites[0], Vector2((32 * life) - 12, -12), 0.0, 2.0, WHITE)

        for life in range(LIFE_COUNT - livesLeft):
            endOfHealthbar = 32 * (LIFE_COUNT - 1)
            lifeToPixel = (32 * life) + 12
            draw_texture_ex(heartSprites[1], Vector2(endOfHealthbar - lifeToPixel, -12), 0.0, 2.0, WHITE)

        draw_text(f"SCORE: {score}", 10, 42, 20, DARKPURPLE)
        draw_text(f"HI: {highScore}", 10, 62, 20, DARKPURPLE)
        draw_text(f"SCORE: {score}", 8, 40, 20, MAGENTA)
        draw_text(f"HI: {highScore}", 8, 60, 20, MAGENTA)

        # End the frame
        end_drawing()

        # Update the frame count, delta time, game uptime, and FPS values
        frameCount += 1
        deltaTime = get_frame_time()
        uptime += deltaTime
        FPS = get_fps()

        # Update the high score
        if score > highScore:
            highScore = score

        # Update the score when ready
        if uptime >= lastScoreUpdate:
            lastScoreUpdate = uptime + (SCORE_INCREASE_INTERVAL_MS / 1000)
            score += 1

        # Update the title when ready
        if uptime >= lastTitleUpdate:
            lastTitleUpdate = uptime + (TITLE_UPDATE_INTERVAL_MS / 1000)
            set_window_title(f"{GAME_NAME} | {WINDOW_WIDTH}x{WINDOW_HEIGHT} | {FPS} FPS")

        # Get this program's resource usage when ready, and debugging is enabled
        if enableDebug == True and uptime >= lastResourceUsageUpdate:
            lastResourceUsageUpdate = uptime + (RESOURCE_USAGE_UPDATE_INTERVAL_MS / 1000)
            cpuUsage = currentProcess.cpu_percent(interval=None) / psutil.cpu_count()
            memUsageKB = currentProcess.memory_info().rss / 1024

except Exception as EX:
    print(f"[ERROR:MAIN] >> Error in window loop: {EX}")

# Clean up
print("[INFO:MAIN] >> Game loop exited, cleaning up...")
print(" ╰───╼ Unloading sprite(s)...")
for sprite in heartSprites:
    unload_texture(sprite)

# Close the game window
print("\n[INFO:MAIN] >> Closing game window...")
close_window()

# Write the user's high score to a file
print(f"[INFO:MAIN] >> Saving game stats to \"{STATS_FILE}\"...")
try:
    with open(STATS_FILE, 'w') as StatsFile:
        StatsFile.write(f"HI={highScore}\n")

except Exception as EX:
    print(f"[ERROR:MAIN] >> Failed to write to \"{STATS_FILE}\": {EX}")

# Call the garbage collector
print("[INFO:MAIN] >> Running final garbage collection...")
collectedObjects = gc.collect()
print(f" ╰───╼ Collected {collectedObjects} objects\n")

print("[INFO:MAIN] >> Exiting...")
