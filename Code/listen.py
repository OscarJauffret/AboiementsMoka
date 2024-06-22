import os
import pygame
import InquirerPy
import numpy as np
from db_requests import insert_known_bark

pygame.mixer.init()

keep_file = {"name": "Keep", "type": "list", "message": "Voulez-vous conserver ce fichier audio ?", "choices": ["Oui", "Non"]}

def play_audio(file_path):
    if os.path.exists(file_path):
        pygame.mixer.music.load(file_path)
        pygame.mixer.music.play()
        print(f"Playing audio from {file_path}")

def fourier_transform(indata):
    signal_fft = np.fft.fft(indata)
    signal_fft_power = np.abs(signal_fft)/len(indata)

    return signal_fft_power

def flatten_signal(indata):
    data = []
    for i in indata:
        data.append(i[0])
    return data

def save_bark(file_path):
    with open(file_path, "rb") as f:
        indata = eval(f.read())
    indata = flatten_signal(indata)
    power = fourier_transform(indata)
    harmonics = get_highest_harmonics(power)
    insert_known_bark(harmonics)

def get_highest_harmonics(power, threshold_ratio=0.1):
    harmonics = []
    max_amplitude = np.max(power)
    power_normalized = power / max_amplitude
    for i in range(1, len(power_normalized) // 2):
        if power_normalized[i] > threshold_ratio:
            harmonics.append((i, power_normalized[i]))
    return harmonics

if __name__ == "__main__":
    for file in os.listdir("./barks"):
        if file.endswith(".wav"):
            file_path = os.path.join("./barks", file)
            play_audio(file_path)
            while pygame.mixer.music.get_busy():
                continue
            answer = InquirerPy.prompt(keep_file)
            if answer == "Non":
                os.remove(file_path)
            else:
                save_bark(file_path)
                os.remove(file_path)
