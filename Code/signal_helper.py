import random
import numpy as np


def generate_random_sine_wave(signal_span):
    freq = random.randint(1, 10)
    amplitude = random.randint(1, 10)
    print(f"Frequency: {freq} Hz, Amplitude: {amplitude}")
    return amplitude * np.sin(freq * signal_span)


def generate_random_signal(signal_span):
    signal = np.zeros_like(signal_span)
    for i in range(15):
        signal += generate_random_sine_wave(signal_span)

    #for i in range(5):
    #    signal += 0.01 * np.sin(random.randint(1, 30) * signal_span)
    return signal


def reconstruct_signal_based_on_harmonics(signal_fft_power, signal_span):
    harmonics = get_highest_harmonics(signal_fft_power)
    reconstructed_signal = np.zeros_like(signal_span)
    for harmo in harmonics:
        frequency_index = harmo[0]
        amplitude = harmo[1] * 2
        #reconstructed_signal += amplitude * np.sin(frequency_index / len(signal_span) * signal_span)
        reconstructed_signal += amplitude * np.sin(2 * np.pi * frequency_index / len(signal_span) * signal_span)
    return reconstructed_signal

def get_highest_harmonics(power, threshold_ratio=0.1):
    harmonics = []
    max_amplitude = np.max(power)
    power_normalized = power / max_amplitude
    max_pwr = np.max(power_normalized)
    for i in range(1, len(power_normalized) // 2):
        if power_normalized[i] > threshold_ratio * max_pwr:
            harmonics.append((i, power[i]))
    return harmonics