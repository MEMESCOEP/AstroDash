from pyray import *

loadedTextures = []
loadedMusic = []
loadedSFX = []

def LoadTexture(filePath):
    loadedTextures.append(load_texture(filePath))
    return loadedTextures[-1]

def LoadMusic(filePath):
    loadedMusic.append(load_music_stream(filePath))
    return loadedMusic[-1]

def LoadSoundEffect(filePath):
    loadedSFX.append(load_sound(filePath))
    return loadedSFX[-1]

def UpdateMusicStreams():
    for musicStream in loadedMusic:
        UpdateMusicStream(musicStream)
