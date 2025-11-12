import subprocess
import sys

packageList = ["nuitka", "pymunk", "raylib", "psutil"]

for package in packageList:
    print(f">>> Installing \"{package}\"...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", package] + sys.argv[1:])
    print()
