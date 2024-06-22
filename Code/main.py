import sounddevice as sd
import numpy as np
from scipy.io.wavfile import write
from datetime import datetime
import pygame
import os

class BarkListener:
    def __init__(self):
        pygame.mixer.init()
        self.played_sound_recently = False
        self.noise_threshold = 10  # Ajustez ce seuil selon vos besoins
        self.sample_rate = 44100  # Ajustez selon le taux d'échantillonnage que vous utilisez
        print("Bark detector initialized.")

    def energy_to_db(self, energy):
        return 10 * np.log10(energy / 1.0)

    def detect_bark(self, indata, frames, time, status):
        energy = np.sum(np.square(indata))
        volume = self.energy_to_db(energy)
        if volume > self.noise_threshold and not self.played_sound_recently:
            print(f"Bark detected with volume: {volume}")
            self.save_indata(indata)
            self.played_sound_recently = True
            # Réinitialiser après un délai
            sd.sleep(2000)  # 2 secondes de délai
            self.played_sound_recently = False

    def save_indata(self, indata):
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        file_path = f"./barks/{timestamp}.wav"
        write(file_path, self.sample_rate, indata)  # Enregistrer les données audio dans un fichier WAV
        print(f"Audio saved to {file_path}")


if __name__ == "__main__":
    os.makedirs("./barks", exist_ok=True)  # Créer le dossier de stockage des fichiers audio s'il n'existe pas
    bark_listener = BarkListener()
    with sd.InputStream(callback=bark_listener.detect_bark, channels=1, samplerate=44100):
        print("Enregistrement en cours. Appuyez sur Ctrl+C pour arrêter.")
        try:
            while True:
                sd.sleep(1000)
        except KeyboardInterrupt:
            print("Enregistrement arrêté.")
