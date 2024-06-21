import socket
from BarkDetector import BarkDetector
from datetime import datetime
import os
import threading
from db_requests import get_parameters, modify_parameters
import sounddevice as sd
from BarkDetector import SAMPLE_RATE


class Server:

    def __init__(self, bark_detector):
        self.bark_detector = bark_detector
        self.connections = []
        self.current_instance = None
        self.stop_event = threading.Event()
        self.start()

    def start(self):
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.bind(('', 8081))  # Port 8081 utilisé
        server_socket.listen(5)
        print("Server is listening on port 8081")

        while True:
            try:
                client_socket, client_address = server_socket.accept()
                self.connections.append(client_socket)
                print(f"Connection from {client_address}")
                client_thread = threading.Thread(target=self.handle_client, args=(client_socket,))
                client_thread.start()
            except KeyboardInterrupt:
                break

        for connection in self.connections:
            connection.close()
        server_socket.close()

    def handle_client(self, client_socket):
        try:
            while True:
                # Lire la commande ou le type de données
                header = client_socket.recv(1024).decode()
                if not header:
                    break
                print(header)

                if header == "AUDIO_FILE":
                    self.receive_file(client_socket)
                else:
                    self.process(header, client_socket)
        finally:
            print("Connection closed.")
            self.connections.remove(client_socket)
            client_socket.close()

    def receive_file(self, client_socket):
        file_data = b''
        while True:
            data = client_socket.recv(1024)
            if not data or 'END_OF_FILE' in data.decode():
                sender = data.split(b'END_OF_FILE_')[1].decode()
                break
            file_data += data

        path = f'./audio/{sender}'
        os.makedirs(path, exist_ok=True)

        print(f"File received from {sender}")
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        file_name = f'./audio/{sender}/audio_{timestamp}.m4a'
        with open(file_name, 'wb') as f:
            f.write(file_data)
        print(f"File received and saved as '{file_name}'")
        self.bark_detector.update_audio_files()
        self.bark_detector.manual_message()

    def process(self, message, client):
        print(f"Received message: {message}")
        match message:
            case "0":  # éteindre le programme
                self.stop_program()
            case "1":  # allumer le programme
                self.start_program()
            case "2":
                self.bark_detector.manual_message()
            case message if message.startswith("3"):
                received_thresholds = eval(message.split(" ", maxsplit=1)[1])
                new_db_threshold = received_thresholds[0]
                new_resemblance_threshold = received_thresholds[1]
                new_cooldown = received_thresholds[2]
                self.bark_detector.set_thresholds(new_db_threshold, new_resemblance_threshold, new_cooldown)
                modify_parameters([("noise_threshold", new_db_threshold), ("resemblance_threshold", new_resemblance_threshold), ("cooldown", new_cooldown)])
            case "REQUEST_PARAMETERS":
                parameters = get_parameters()
                parameters = str(parameters) + "END_OF_MESSAGE"
                print(parameters)
                client.send(parameters.encode())
            case "REQUEST_APP_STATE":
                if self.current_instance is None:
                    message = "0"
                else:
                    message = "1"
                message += "END_OF_MESSAGE"
                client.send(message.encode())
            case _:
                print("Unhandled message.")

    def start_program(self):
        self.bark_detector = BarkDetector()
        self.current_instance = threading.Thread(target=self.start_detection, args=(self.bark_detector,))
        self.current_instance.start()

    def start_detection(self, bark_detector: BarkDetector):
        with sd.InputStream(callback=bark_detector.detect_bark, channels=1, device=2, samplerate=SAMPLE_RATE):
            print("Enregistrement en cours. Appuyez sur Ctrl+C pour arrêter.")
            try:
                while not self.stop_event.is_set():
                    print(self.stop_event)
                    sd.sleep(1000)
            except KeyboardInterrupt:
                print("Enregistrement arrêté.")
            print("Détection arretée")

    def stop_program(self):
        self.stop_event.set()
        self.current_instance.join()  # Attendre que le thread se termine
        self.current_instance = None
        self.stop_event.clear()


if __name__ == "__main__":
    server = Server(BarkDetector())
