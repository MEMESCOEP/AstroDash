from raylib._raylib_cffi import ffi
from pyray import load_texture, load_music_stream, load_sound, update_music_stream, unload_texture, unload_music_stream, unload_sound
import MessageBox

loadedTextures = []
loadedMusic = []
loadedSFX = []
ShowLoadErrors = True

def LoadTexture(filePath):
    loadedTextures.append(load_texture(filePath))

    if ShowLoadErrors == True and loadedTextures[-1].id == 0:
        MessageBox.showMessage(MessageBox.MessageTypes.ERROR, "Failed to load texture file", f"Failed to load the texture \"{filePath}\"")

    return loadedTextures[-1]

def LoadMusic(filePath):
    loadedMusic.append(load_music_stream(filePath))

    if ShowLoadErrors == True and loadedMusic[-1].stream.buffer == ffi.NULL:
        MessageBox.showMessage(MessageBox.MessageTypes.ERROR, "Failed to load music file", f"Failed to load the music file \"{filePath}\"")

    return loadedMusic[-1]

def LoadSoundEffect(filePath):
    loadedSFX.append(load_sound(filePath))

    if ShowLoadErrors == True and loadedSFX[-1].stream.buffer == ffi.NULL:
        MessageBox.showMessage(MessageBox.MessageTypes.ERROR, "Failed to load sound effect file", f"Failed to load the sound effect file \"{filePath}\"")

    return loadedSFX[-1]

def UnloadAllAssets():
    print(f" ├───╼ Unloading {len(loadedTextures)} textures(s)...")
    for texture in loadedTextures:
        unload_texture(texture)

    print(f" ├───╼ Unloading {len(loadedMusic)} music file(s)...")
    for musicFile in loadedMusic:
        unload_music_stream(musicFile)

    print(f" ╰───╼ Unloading {len(loadedSFX)} sound(s)...")
    for soundEffect in loadedSFX:
        unload_sound(soundEffect)

    print()

def UpdateMusicStreams():
    for musicStream in loadedMusic:
        update_music_stream(musicStream)
