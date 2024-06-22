import socket
from BarkDetector import BarkDetector
from datetime import datetime
import os
import threading
from db_requests import get_parameters, modify_parameters, get_last_barks
import sounddevice as sd
from BarkDetector import SAMPLE_RATE
import locale


locale.setlocale(locale.LC_TIME, 'fr_FR.UTF-8')


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
        #self.bark_detector.manual_message()

    def process(self, message, client):
        print(f"Received message: {message}")
        match message:
            case "0":  # éteindre le programme
                self.stop_program()
            case "1":  # allumer le programme
                self.start_program()
            case message if message.startswith("2"):
                received_voice = eval(message.split(" ", maxsplit=1)[1])
                self.bark_detector.manual_detection(received_voice)
            case message if message.startswith("3"):
                received_thresholds = eval(message.split(" ", maxsplit=1)[1])
                new_db_threshold = received_thresholds[0]
                new_resemblance_threshold = received_thresholds[1]
                new_cooldown = received_thresholds[2]
                self.bark_detector.set_thresholds(new_db_threshold, new_resemblance_threshold, new_cooldown)
                modify_parameters([("noise_threshold", new_db_threshold), ("resemblance_threshold", new_resemblance_threshold), ("cooldown", new_cooldown)])
            case "REQUEST_PARAMETERS":
                parameters = get_parameters()
                parameters = self.format_parameters(parameters)
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
            case "REQUEST_LAST_BARKS":
                last_barks = get_last_barks()
                last_barks = self.format_last_barks(last_barks)
                last_barks = str(last_barks) + "END_OF_MESSAGE"
                client.send(last_barks.encode())
            case _:
                print("Unhandled message.")

    def format_parameters(self, parameters):
        formatted_parameters = ""
        for param in parameters:
            formatted_parameters += f"{param[1]}:{param[2]}, "
        return formatted_parameters[:-2]

    def format_last_barks(self, last_barks):
        formatted_barks = ""
        translate_mode = {"Automatic": "Automatique", "Manual": "Manuel", "Not handled": "Non traité"}
        for bark in last_barks:
            formatted_barks += f"{self.format_timestamp(bark[0])};{translate_mode[str(bark[1]).capitalize()]};{bark[2]}? "
        return formatted_barks[:-2]

    def format_timestamp(self, timestamp):
        # Convertir le timestamp en objet datetime
        dt = datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S')
        # Formater la date et l'heure
        formatted_date = dt.strftime('%d %B, %Hh%M')
        return formatted_date

    def start_program(self):
        self.bark_detector = BarkDetector()
        self.current_instance = threading.Thread(target=self.start_detection, args=(self.bark_detector,))
        self.current_instance.start()

    def start_detection(self, bark_detector: BarkDetector):
        with sd.InputStream(callback=bark_detector.detect_bark, channels=1, device=0, samplerate=SAMPLE_RATE):
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
