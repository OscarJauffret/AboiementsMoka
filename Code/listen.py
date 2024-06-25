import os
import pygame
import InquirerPy
import numpy as np
from db_requests import insert_known_bark
from matplotlib import pyplot as plt

pygame.mixer.init()

keep_file = {"name": "Keep", "type": "list", "message": "Voulez-vous conserver ce fichier audio ?", "choices": ["Oui", "Non"]}

def play_audio(file_path):
    if os.path.exists(file_path):
        pygame.mixer.music.load(file_path)
        pygame.mixer.music.play()
        print(f"Playing audio from {file_path}")
        while pygame.mixer.music.get_busy():
            pygame.time.Clock().tick(10)  # Attendre que la lecture soit terminée
        pygame.mixer.music.stop()
        pygame.mixer.music.unload()

def fourier_transform(indata):
    signal_fft = np.fft.fft(indata)
    signal_fft_power = np.abs(signal_fft)/len(indata)

    return signal_fft_power


def save_bark(file_path):
    with open(file_path, "rb") as f:
        indata = eval(f.read())
    power = fourier_transform(indata)
    plot_data(power)
    harmonics = get_highest_harmonics(power)
    #print(len(harmonics))
    insert_known_bark(harmonics)

def plot_data(power):
    plt.plot(power, 'o', label="power")
    plt.legend()
    plt.show()

def get_highest_harmonics(power, threshold_ratio=0.6):
    harmonics = []
    max_amplitude = np.max(power)
    power_normalized = power / max_amplitude
    for i in range(1, len(power_normalized) // 2):
        if power_normalized[i] > threshold_ratio:
            frequency = i * 44100 / len(power_normalized)
            harmonics.append((frequency, power_normalized[i]))
            #harmonics.append((i, power_normalized[i]))
    return harmonics

if __name__ == "__main__":
    for file in os.listdir("./barks"):
        if file.endswith(".wav"):
            timestamp = file.split("_", maxsplit=1)[1].split(".")[0]
            print(f"Playing audio from {timestamp}")
            file_path = os.path.join("./barks", file)
            buffer_path = os.path.join("./barks", f"buffer_{timestamp}.txt")
            play_audio(file_path)
            while pygame.mixer.music.get_busy():
                continue
            answer = InquirerPy.prompt(keep_file)
            if answer["Keep"] == "Oui":
                save_bark(buffer_path)
            os.remove(file_path)
            os.remove(buffer_path)
