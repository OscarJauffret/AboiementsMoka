import sounddevice as sd
import numpy as np
from scipy.io.wavfile import write
from datetime import datetime
import pygame
import os
import threading
from collections import deque

class BarkListener:
    def __init__(self):
        pygame.mixer.init()
        self.played_sound_recently = False
        self.noise_threshold = 10  # Ajustez ce seuil selon vos besoins
        self.sample_rate = 44100  # Ajustez selon le taux d'échantillonnage que vous utilisez
        self.bark_duration = 1  # Durée de l'enregistrement en secondes
        self.bark_number = 0
        self.buffer = []  # Tampon pour stocker les données audio avant l'enregistrement
        self.previous_buffer = deque(maxlen=22050)  # Tampon pour stocker les données audio avant le déclenchement
        print("Bark detector initialized.")

    def energy_to_db(self, energy):
        return 10 * np.log10(energy / 1.0)

    def detect_bark(self, indata, frames, time, status):
        # Ajouter les données audio au tampon
        if not self.played_sound_recently:
            self.previous_buffer.extend(indata[:, 0])
        if self.played_sound_recently:
            self.buffer.extend(indata[:, 0])

        energy = np.sum(np.square(indata))
        volume = self.energy_to_db(energy)
        if volume > self.noise_threshold and not self.played_sound_recently:
            print(f"Bark detected with volume: {volume}")
            self.played_sound_recently = True
            threading.Timer(self.bark_duration, self.save_indata).start()

    def save_indata(self):
        self.played_sound_recently = False
        self.buffer = list(self.previous_buffer) + self.buffer
        if len(self.buffer) == 0:
            return
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        file_path = f"./barks/bark_{timestamp}_{self.bark_number}.wav"
        buffer_path = f"./barks/buffer_{timestamp}_{self.bark_number}.txt"
        # Convertir le tampon en numpy array et sauvegarder
        audio_data = np.array(self.buffer, dtype=np.float32)
        audio_data = np.int16(audio_data / np.max(np.abs(audio_data)) * 32767)
        write(file_path, self.sample_rate, audio_data)
        print(f"Audio saved to {file_path}")
        # Sauvegarder le tampon pour analyse
        with open(buffer_path, "w") as f:
            f.write(str(self.buffer))
        self.previous_buffer.extend(self.buffer)
        self.buffer = []  # Réinitialiser le tampon
        self.bark_number += 1


if __name__ == "__main__":
    os.makedirs("./barks", exist_ok=True)  # Créer le dossier de stockage des fichiers audio s'il n'existe pas
    bark_listener = BarkListener()
    with sd.InputStream(callback=bark_listener.detect_bark, channels=1, samplerate=44100, device=1):
        print("Enregistrement en cours. Appuyez sur Ctrl+C pour arrêter.")
        try:
            while True:
                sd.sleep(1000)
        except KeyboardInterrupt:
            print("Enregistrement arrêté.")
