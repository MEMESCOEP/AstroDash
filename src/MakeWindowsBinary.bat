@echo off
REM Set build directory and executable name
set "BUILD_DIR=%cd%\bin"
set "EXE_NAME=Game.exe"

echo ^>^>^> Creating Windows executable "%BUILD_DIR%\%EXE_NAME%"...

REM Create build directory if it doesn't exist
if not exist "%BUILD_DIR%" mkdir "%BUILD_DIR%"

REM Compile with Nuitka using MSVC
python -m nuitka ^
    --standalone ^
    --onefile ^
    --lto=yes ^
    --jobs=%NUMBER_OF_PROCESSORS% ^
    --python-flag=-O ^
    --output-file="%EXE_NAME%" ^
    --output-dir="%BUILD_DIR%" ^
    --assume-yes-for-downloads ^
    --msvc=latest ^
    Game.py