import numpy as np
import os
import random
import matplotlib.pyplot as plt
from db_requests import get_known_barks, get_parameters, insert_bark
from time import sleep
import threading
from collections import deque
from pydub import AudioSegment
from pydub.playback import play
from datetime import datetime

SAMPLE_RATE = 44100


class BarkDetector:

    def __init__(self):
        self.played_sound_recently = False
        self.audio_files = None
        self.available_voices = ["Papa", "Maman", "Héloïse", "Oscar", "Augustine"]
        self.update_audio_files()
        self.ref_E = 1.0
        self.min_time_between_audio = 120
        self.noise_threshold = 10
        self.harmonic_resemblance_threshold = 0.5
        self.amplitude_resemblance_threshold = 0.9
        self.resemblance_threshold = 0.4
        self.delay_before_message = 2
        self.detected_sound_recently = False
        self.buffer = []  # Tampon pour stocker les données audio avant l'enregistrement
        self.previous_buffer = deque(maxlen=22050)  # Tampon pour stocker les données audio avant le déclenchement
        print("Bark detector initialized.")

    def update_audio_files(self):
        self.audio_files = self._list_files("./audio")
        print("Audio files: ", self.audio_files)

    def initialize_thresholds(self):
        parameters = get_parameters()
        for param in parameters:
            if param[0] == "noise_threshold":
                self.noise_threshold = int(param[1])
            elif param[0] == "resemblance_threshold":
                self.resemblance_threshold = float(param[1])
            elif param[0] == "cooldown":
                self.min_time_between_audio = int(param[1])
                self.min_time_between_audio_frames = self.min_time_between_audio * SAMPLE_RATE


    def set_thresholds(self, new_db_threshold, new_resemblance_threshold, new_cooldown):
        self.noise_threshold = int(new_db_threshold)
        self.resemblance_threshold = new_resemblance_threshold
        self.min_time_between_audio = int(new_cooldown)

    def _list_files(self, path):
        files = [[] for _ in range(len(self.available_voices))]
        for i, voice in enumerate(self.available_voices):
            files[i] = self._list_files_for_voice(os.path.join(path, voice))
        return files

    def _list_files_for_voice(self, path):
        if not os.path.exists(path):
            return []
        files = os.listdir(path)
        for i, file in enumerate(files):
            files[i] = os.path.join(path, file)
        return files

    def energy_to_db(self, energy):
        return 10 * np.log10(energy / self.ref_E)

    def fourier_transform(self, indata):
        signal_fft = np.fft.fft(indata)
        signal_fft_power = np.abs(signal_fft)/len(indata)

        return signal_fft_power

    def manual_message(self, voice):
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        insert_bark([timestamp, "Manual", str(voice)])
        self.play_sound(str(voice))

    def detect_bark(self, indata, frames, time, status):
        energy = np.sum(np.square(indata))
        volume = self.energy_to_db(energy)
        if not self.detected_sound_recently:
            self.previous_buffer.extend(indata[:, 0])
        else:
            self.buffer.extend(indata[:, 0])

        if volume > self.noise_threshold and not self.played_sound_recently and not self.detected_sound_recently:
            self.detected_sound_recently = True
            threading.Timer(1, self.reset_detected_sound_recently).start()

    def reset_detected_sound_recently(self):
        self.buffer = list(self.previous_buffer) + self.buffer
        self.detected_sound_recently = False
        self.handle_high_volume(self.buffer)

    def handle_high_volume(self, indata):
        power = self.fourier_transform(indata)
        harmonics = get_highest_harmonics(power)
        #print(f"{harmonics = }")
        if self.compare_with_data(harmonics):
            print("Detected bark at ", datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
            sleep(self.delay_before_message)
            self.played_sound_recently = True
            threading.Timer(self.min_time_between_audio, self.reset_recent_variables).start()
            voice = self.chose_voice()
            insert_bark([datetime.now().strftime('%Y-%m-%d %H:%M:%S'), "Automatic", voice])
            self.play_sound(voice)
        self.buffer = []

    def chose_voice(self):
        voice = random.randint(0, len(self.audio_files) - 1)
        if not self.audio_files[voice]:
            self.chose_voice()
        return self.available_voices[voice]


    def plot_data(self, indata, power):
        plt.plot(indata, label="indata")
        plt.plot(power, 'o', label="power")
        plt.legend()
        plt.show()

    def play_sound(self, voice=None):
        if voice is None:
            voice = random.randint(0, len(self.audio_files) - 1)
        else:
            print("Voice: ", voice, end=" ")
            voice = self.available_voices.index(voice)
            print("It is number: ", voice)

        chosen_file = random.choice(self.audio_files[voice])
        if not chosen_file:
            self.play_sound()
        audio = AudioSegment.from_file(chosen_file, format="m4a")
        play(audio)

    def reset_recent_variables(self):
        self.played_sound_recently = False

    def compare_with_data(self, harmonics):
        known_barks = get_known_barks()
        harmonics = sorted(harmonics, key=lambda x: x[0])
        for i, bark in enumerate(known_barks):
            if self.compare_barks(harmonics, bark):
                print("Bark detected!, Bark ID: ", i + 1)
                return True
        return False

    def compare_barks(self, harmonics, bark):
        found_resemblance = [False for _ in range(len(harmonics))]
        if len(found_resemblance) == 0:
            return
        for i, (harmonic, amplitude) in enumerate(harmonics):
            for bark_harmonic, bark_ampl in bark:
                if self.harmonic_resemblance(harmonic, bark_harmonic) >= self.harmonic_resemblance_threshold:
                    if self.amplitude_resemblance(amplitude, bark_ampl) > self.amplitude_resemblance_threshold:
                        found_resemblance[i] = True
                        break
        if self.enough_resemblance(found_resemblance):
            return True

    def harmonic_resemblance(self, harmonic1, harmonic2):
        harmonic_diff = abs(harmonic1 - harmonic2)
        return 1/harmonic_diff if harmonic_diff != 0 else 1

    def amplitude_resemblance(self, amplitude1, amplitude2, scale=1.0):
        amplitude_diff = abs(amplitude1 - amplitude2)
        return np.exp(-scale * amplitude_diff)

    def enough_resemblance(self, found_resemblance):
        print(sum(found_resemblance)/len(found_resemblance))
        return sum(found_resemblance) / len(found_resemblance) > self.resemblance_threshold


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
    bark_detector = BarkDetector()

