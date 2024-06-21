import sounddevice as sd
from BarkDetector import *
from server import Server


def start_detection(bark_detector: BarkDetector):
    with sd.InputStream(callback=bark_detector.detect_bark, channels=1, device=2, samplerate=SAMPLE_RATE):
        print("Enregistrement en cours. Appuyez sur Ctrl+C pour arrêter.")
        try:
            while True:
                sd.sleep(1000 * 1000)
        except KeyboardInterrupt:
            print("Enregistrement arrêté.")




# if __name__ == "__main__":
#     bark_detector = BarkDetector()
#     server = Server(bark_detector)
#     with sd.InputStream(callback=bark_detector.detect_bark, channels=1, device=2, samplerate=SAMPLE_RATE):
#         print("Enregistrement en cours. Appuyez sur Ctrl+C pour arrêter.")
#         try:
#             while True:
#                 sd.sleep(1000 * 1000)
#         except KeyboardInterrupt:
#             print("Enregistrement arrêté.")