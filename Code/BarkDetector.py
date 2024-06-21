import numpy as np
import pygame
import os
import random
import matplotlib.pyplot as plt
from signal_helper import generate_random_signal, reconstruct_signal_based_on_harmonics
from db_requests import get_known_barks, get_parameters
from time import sleep

SAMPLE_RATE = 44100

class BarkDetector:

    def __init__(self):
        pygame.mixer.init()
        self.played_sound_recently = False
        self.audio_files = None
        self.available_voices = ["Papa", "Maman", "Héloïse", "Oscar", "Augustine"]
        self.update_audio_files()
        self.time_since_last_play = 0
        self.ref_E = 1.0
        self.min_time_between_audio = 120
        self.noise_threshold = 10
        self.harmonic_resemblance_threshold = 0.5
        self.amplitude_resemblance_threshold = 0.9
        self.resemblance_threshold = 0.7
        self.delay_before_message = 2
        self.min_time_between_audio_frames = self.min_time_between_audio * SAMPLE_RATE
        print("Bark detector initialized.")

    def update_audio_files(self):
        self.audio_files = self._list_files("./audio")

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
        self.min_time_between_audio_frames = self.min_time_between_audio * SAMPLE_RATE

    def _list_files(self, path):
        files = []
        for voice in self.available_voices:
            files.extend(self._list_files_for_voice(os.path.join(path, voice)))
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

    def manual_message(self):
        self.play_sound()

    def flatten_signal(self, indata):
        data = []
        for i in indata:
            data.append(i[0])
        return data


    def detect_bark(self, indata, frames, time, status):
        energy = np.sum(np.square(indata))
        volume = self.energy_to_db(energy)
        self.check_played_recently(volume)
        if (volume > self.noise_threshold) and not self.played_sound_recently:
            indata = self.flatten_signal(indata)
            power = self.fourier_transform(indata)
            harmonics = get_highest_harmonics(power)
            print(f"{harmonics = }")
            if self.compare_with_data(harmonics):
                self.played_sound_recently = True
                self.time_since_last_play = 0
                self.play_sound()

    def plot_data(self, indata, power):
        plt.plot(indata, label="indata")
        plt.plot(power, 'o', label="power")
        plt.legend()
        plt.show()

    def play_sound(self):
        sleep(self.delay_before_message)
        chosen_voice = random.randint(0, len(self.audio_files) - 1)
        chosen_file = random.choice(self.audio_files[chosen_voice])
        if not chosen_file:
            self.play_sound()
        chosen_file = "./audio/nopeeking.mp3"
        #print(f"Playing {chosen_file}")
        pygame.mixer.music.load(chosen_file)
        pygame.mixer.music.play()
        if chosen_file.split(".")[1] == "m4a":
            while pygame.mixer.music.get_busy():  # wait for music to finish playing
                pygame.time.Clock().tick(10)

    def check_played_recently(self, volume):
        if self.played_sound_recently and self.time_since_last_play == 1200:
            self.reset_recent_variables()
        if self.played_sound_recently:
            self.time_since_last_play += 1
        #    print(f"Temps restant : {round(1200 - self.time_since_last_play)}")
        #else:
        #    print(f"{volume = }")

    def reset_recent_variables(self):
        self.played_sound_recently = False
        self.time_since_last_play = 0

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
        return sum(found_resemblance) / len(found_resemblance) > self.resemblance_threshold


def get_highest_harmonics(power, threshold_ratio=0.1):
    harmonics = []
    max_amplitude = np.max(power)
    power_normalized = power / max_amplitude
    for i in range(1, len(power_normalized) // 2):
        if power_normalized[i] > threshold_ratio:
            harmonics.append((i, power_normalized[i]))
    return harmonics


if __name__ == "__main__":
    bark_detector = BarkDetector()

    signal_span = np.r_[0:6*np.pi: np.pi/32]
    signal = generate_random_signal(signal_span)

    #signal = [0.05935669, 0.051635742, 0.042633057, 0.03286743, 0.02355957, 0.012939453, 0.003112793, -0.0069885254, -0.017974854, -0.030212402, -0.03930664, -0.0501709, -0.060760498, -0.07110596, -0.082733154, -0.09213257, -0.10211182, -0.11376953, -0.12310791, -0.13214111, -0.14257812, -0.14929199, -0.1543274, -0.15789795, -0.15994263, -0.16421509, -0.1673584, -0.17071533, -0.17352295, -0.17321777, -0.17553711, -0.17764282, -0.17755127, -0.17700195, -0.17288208, -0.17053223, -0.16680908, -0.16275024, -0.15930176, -0.15341187, -0.14797974, -0.14257812, -0.13674927, -0.13131714, -0.12609863, -0.11987305, -0.11206055, -0.103271484, -0.0947876, -0.08554077, -0.076812744, -0.06781006, -0.05987549, -0.0513916, -0.04272461, -0.032989502, -0.02230835, -0.012298584, -0.0018310547, 0.008605957, 0.019958496, 0.030517578, 0.0418396, 0.053100586, 0.06347656, 0.072753906, 0.0819397, 0.092285156, 0.103515625, 0.11331177, 0.123565674, 0.13317871, 0.14086914, 0.14813232, 0.15158081, 0.1543274, 0.15753174, 0.15881348, 0.1612854, 0.16339111, 0.16488647, 0.16653442, 0.16732788, 0.16830444, 0.16964722, 0.16821289, 0.16494751, 0.16217041, 0.1574707, 0.15325928, 0.1482544, 0.14361572, 0.13919067, 0.1338501, 0.12908936, 0.12307739, 0.11734009, 0.109313965, 0.10180664, 0.093048096, 0.08520508, 0.07763672, 0.06866455, 0.06109619, 0.052886963, 0.045562744, 0.036621094, 0.026672363, 0.018341064, 0.009674072, -0.0005187988, -0.010406494, -0.020050049, -0.03060913, -0.04031372, -0.051086426, -0.059906006, -0.068878174, -0.07891846, -0.087127686, -0.09713745, -0.10656738, -0.114746094, -0.123046875, -0.1296997, -0.13665771, -0.14007568, -0.1434021, -0.14633179, -0.14846802, -0.152771, -0.15444946, -0.15438843, -0.15628052, -0.15805054, -0.16009521, -0.15969849, -0.15762329, -0.15420532, -0.15081787, -0.14797974, -0.14501953, -0.1402893, -0.13552856, -0.13101196, -0.1265564, -0.12188721, -0.115722656, -0.109436035, -0.103881836, -0.096710205, -0.090789795, -0.08407593, -0.075653076, -0.06719971, -0.057678223, -0.050689697, -0.043182373, -0.035064697, -0.026885986, -0.018737793, -0.008392334, 0.0006713867, 0.009460449, 0.017791748, 0.028259277, 0.038909912, 0.049072266, 0.058380127, 0.066223145, 0.07684326, 0.08566284, 0.093566895, 0.102386475, 0.11218262, 0.12036133, 0.1282959, 0.13409424, 0.13955688, 0.14276123, 0.14553833, 0.14807129, 0.15100098, 0.15286255, 0.15420532, 0.15533447, 0.15625, 0.15908813, 0.15985107, 0.15792847, 0.15496826, 0.15219116, 0.14959717, 0.14660645, 0.1437378, 0.13912964, 0.13345337, 0.12814331, 0.12350464, 0.1199646, 0.11315918, 0.10723877, 0.10122681, 0.09310913, 0.08703613, 0.079315186, 0.07070923, 0.06347656, 0.05633545, 0.048095703, 0.04067993, 0.032806396, 0.024627686, 0.0152282715, 0.007537842, -0.0021362305, -0.012237549, -0.020477295, -0.029937744, -0.03817749, -0.04736328, -0.05682373, -0.066467285, -0.07476807, -0.08358765, -0.09182739, -0.0993042, -0.10748291, -0.11413574, -0.11953735, -0.12478638, -0.12869263, -0.1317749, -0.13586426, -0.13867188, -0.14038086, -0.14151001, -0.14260864, -0.14431763, -0.1453247, -0.14550781, -0.14419556, -0.14297485, -0.13952637, -0.13626099, -0.13409424, -0.13052368, -0.1260376, -0.121673584, -0.11758423, -0.1121521, -0.107543945, -0.10235596, -0.09524536, -0.08920288, -0.08392334, -0.0765686, -0.07028198, -0.063201904, -0.054595947, -0.04586792, -0.03756714, -0.029693604, -0.02166748, -0.014190674, -0.005584717, 0.0027770996, 0.01171875, 0.021606445, 0.029724121, 0.03881836, 0.049316406, 0.05871582, 0.06790161, 0.07687378, 0.085113525, 0.09341431, 0.1020813, 0.10946655, 0.1161499, 0.123687744, 0.12908936, 0.13253784, 0.13668823, 0.13842773, 0.14172363, 0.14477539, 0.14550781, 0.14880371, 0.14837646, 0.15014648, 0.15234375, 0.15075684, 0.14923096, 0.14782715, 0.14413452, 0.14050293, 0.13815308, 0.13348389, 0.12911987, 0.12490845, 0.12036133, 0.114990234, 0.10961914, 0.1031189, 0.0975647, 0.091308594, 0.083984375, 0.07611084, 0.067993164, 0.061309814, 0.0541687, 0.047454834, 0.037963867, 0.029724121, 0.023254395, 0.013916016, 0.0054626465, -0.0035095215, -0.011627197, -0.021606445, -0.03060913, -0.039123535, -0.049194336, -0.056915283, -0.06655884, -0.07571411, -0.08358765, -0.09207153, -0.10003662, -0.10821533, -0.11514282, -0.12106323, -0.12554932, -0.12896729, -0.13140869, -0.13446045, -0.1381836, -0.14041138, -0.1425476, -0.14331055, -0.14480591, -0.14602661, -0.14660645, -0.14562988, -0.14379883, -0.14004517, -0.13800049, -0.13555908, -0.13110352, -0.12820435, -0.12277222, -0.1182251, -0.114471436, -0.109436035, -0.10354614, -0.09667969, -0.089660645, -0.08377075, -0.07702637, -0.07046509, -0.062805176, -0.05404663, -0.045166016, -0.036895752, -0.030639648, -0.022155762, -0.014221191, -0.005340576, 0.006134033, 0.014923096, 0.0234375, 0.031829834, 0.042022705, 0.051696777, 0.06124878, 0.071502686, 0.08093262, 0.089019775, 0.09902954, 0.107910156, 0.11569214, 0.12512207, 0.13043213, 0.13790894, 0.14151001, 0.14483643, 0.14978027, 0.1503601, 0.15460205, 0.15567017, 0.15670776, 0.15896606, 0.16079712, 0.16201782, 0.16156006, 0.15975952, 0.15823364, 0.15649414, 0.15341187, 0.15032959, 0.14468384, 0.14147949, 0.13644409, 0.1317749, 0.12734985, 0.12164307, 0.11630249, 0.10897827, 0.10256958, 0.09603882, 0.087677, 0.07937622, 0.0730896, 0.06588745, 0.05734253, 0.0496521, 0.04196167, 0.03375244, 0.025268555, 0.016082764, 0.006866455, -0.0030517578, -0.012634277, -0.022583008, -0.031585693, -0.04168701, -0.050964355, -0.059783936, -0.069366455, -0.07748413, -0.08660889, -0.095062256, -0.10424805, -0.11218262, -0.12011719, -0.12588501, -0.12991333, -0.13421631, -0.13659668, -0.1399231, -0.14324951, -0.14578247, -0.14746094, -0.14755249, -0.14889526, -0.15048218, -0.15209961, -0.14953613, -0.14736938, -0.14520264, -0.14141846, -0.13809204, -0.13458252, -0.13082886, -0.12615967, -0.121276855, -0.11642456, -0.1109314, -0.10446167, -0.09906006, -0.092559814, -0.08682251, -0.07998657, -0.072265625, -0.06384277, -0.053955078, -0.045928955, -0.0390625, -0.03125, -0.023132324, -0.014892578, -0.004486084, 0.0059814453, 0.014221191, 0.023803711, 0.03387451, 0.044647217, 0.055236816, 0.064331055, 0.07357788, 0.08282471, 0.092437744, 0.10168457, 0.11102295, 0.119140625, 0.12677002, 0.1350708, 0.14083862, 0.14395142, 0.14752197, 0.15118408, 0.15374756, 0.15621948, 0.15914917, 0.16033936, 0.1618042, 0.1640625, 0.16397095, 0.16329956, 0.16241455, 0.15975952, 0.15759277, 0.15362549, 0.15014648, 0.14575195, 0.14099121, 0.137146, 0.13168335, 0.12683105, 0.12057495, 0.11462402, 0.10836792, 0.10092163, 0.09378052, 0.08544922, 0.077545166, 0.07052612, 0.062438965, 0.05456543, 0.04598999, 0.036499023, 0.029510498, 0.019927979, 0.00982666, 0.00030517578, -0.008148193, -0.0184021, -0.028442383, -0.03729248, -0.048217773, -0.057891846, -0.06695557, -0.076416016, -0.08673096, -0.094451904, -0.103881836, -0.11251831, -0.11953735, -0.12789917, -0.13272095, -0.1357727, -0.13909912, -0.14199829, -0.1458435, -0.14880371, -0.14953613, -0.1512146, -0.15332031, -0.15429688, -0.15670776, -0.15618896, -0.15270996, -0.14923096, -0.14761353, -0.14352417, -0.14160156, -0.13677979, -0.13192749, -0.12762451, -0.122161865, -0.116882324, -0.1109314, -0.10501099, -0.09866333, -0.092041016, -0.08569336, -0.078430176, -0.068237305, -0.06036377, -0.051086426, -0.044128418, -0.036346436, -0.029266357, -0.019836426, -0.009338379, 0.00024414062, 0.0105896, 0.01852417, 0.028381348, 0.039489746, 0.05038452, 0.06137085, 0.07009888, 0.07980347, 0.089782715, 0.09967041, 0.11004639, 0.119506836, 0.1279602, 0.13632202, 0.14172363, 0.14764404, 0.15197754, 0.15478516, 0.15911865, 0.16168213, 0.1633606, 0.16421509, 0.16610718, 0.1689148, 0.17098999, 0.1706543, 0.16958618, 0.1671753, 0.16348267, 0.16204834, 0.1585083, 0.15270996, 0.14929199, 0.14492798, 0.1404419, 0.1355896, 0.12893677, 0.12200928, 0.11520386, 0.10891724, 0.101623535, 0.09463501, 0.08590698, 0.078186035, 0.069000244, 0.059448242, 0.05291748, 0.0446167, 0.03543091, 0.025421143, 0.017333984, 0.0078125, -0.0035705566, -0.011993408, -0.02355957, -0.03378296, -0.044281006, -0.05593872, -0.06442261, -0.07333374, -0.08206177, -0.09176636, -0.10107422, -0.10992432, -0.11868286, -0.1279602, -0.13458252, -0.13916016, -0.14370728, -0.14587402, -0.15045166, -0.15286255, -0.15505981, -0.15750122, -0.15805054, -0.1593628, -0.16073608, -0.1619873, -0.16049194, -0.15750122, -0.15466309, -0.15097046, -0.1481018, -0.14398193, -0.14007568, -0.13479614, -0.12860107, -0.12359619, -0.1187439, -0.11383057, -0.108551025, -0.102752686, -0.09515381, -0.088653564, -0.07946777, -0.07009888, -0.06048584, -0.052459717, -0.04345703, -0.036346436, -0.02746582, -0.01663208, -0.0059814453, 0.004180908, 0.012908936, 0.023101807, 0.034179688, 0.04486084, 0.05596924, 0.06573486, 0.076049805, 0.08627319, 0.09680176, 0.10662842, 0.11627197, 0.1257019, 0.1338501, 0.14257812, 0.14834595, 0.15319824, 0.15618896, 0.15982056, 0.16259766, 0.16577148, 0.16720581, 0.16879272, 0.17095947, 0.17321777, 0.17416382, 0.17422485, 0.17340088, 0.17007446, 0.16830444, 0.16400146, 0.16030884, 0.15670776, 0.15093994, 0.14544678, 0.14138794, 0.13562012, 0.12982178, 0.1237793, 0.115722656, 0.107177734, 0.09954834, 0.092681885, 0.083862305, 0.07595825, 0.06677246, 0.058380127, 0.05014038, 0.040985107, 0.03149414, 0.021728516, 0.012268066, 0.0030212402, -0.0077209473, -0.019348145, -0.029510498, -0.04135132, -0.05102539, -0.061584473, -0.07110596, -0.080322266, -0.091156006, -0.10028076, -0.11026001, -0.11972046, -0.12866211, -0.13684082, -0.14407349, -0.14627075, -0.14920044, -0.153656, -0.15661621, -0.16046143, -0.16271973, -0.16397095, -0.16500854, -0.16738892, -0.16897583, -0.16732788, -0.16723633, -0.1637268, -0.16003418, -0.15719604, -0.15466309, -0.14944458, -0.14370728, -0.13928223, -0.13378906, -0.12911987, -0.124298096, -0.11682129, -0.10977173, -0.10357666, -0.09609985, -0.088409424, -0.07965088, -0.07098389, -0.060394287, -0.053588867, -0.044647217, -0.036834717, -0.026733398, -0.015258789, -0.0057678223, 0.005126953, 0.014404297, 0.025482178, 0.036346436, 0.04751587, 0.057861328, 0.06802368, 0.079315186, 0.08999634, 0.10110474, 0.11087036, 0.12045288, 0.13116455, 0.14031982, 0.14849854, 0.15319824, 0.15713501, 0.1607666, 0.16433716, 0.16741943, 0.16970825, 0.17150879, 0.17340088, 0.1767273, 0.17797852, 0.17816162, 0.1781311, 0.17510986, 0.1730957, 0.16949463, 0.165802, 0.16253662, 0.15679932, 0.15148926, 0.14602661, 0.14074707, 0.13589478, 0.12957764, 0.12142944, 0.11340332, 0.10473633, 0.09689331, 0.088378906, 0.07913208, 0.072265625, 0.06311035, 0.05404663, 0.045043945, 0.036193848, 0.027496338, 0.017242432, 0.0065307617, -0.004333496, -0.013214111, -0.024902344, -0.036468506, -0.045806885, -0.057250977, -0.06713867, -0.07711792, -0.08734131, -0.09799194, -0.10739136, -0.11651611, -0.12637329, -0.1354065, -0.14178467, -0.14767456, -0.15161133, -0.15454102, -0.15927124, -0.16217041, -0.1666565, -0.16799927, -0.16882324, -0.17108154, -0.17263794, -0.174469, -0.17245483, -0.17047119, -0.16763306, -0.16323853, -0.16113281, -0.15597534, -0.15097046, -0.14697266, -0.14105225, -0.13607788, -0.1308899, -0.12484741, -0.11795044, -0.11117554, -0.10372925, -0.09429932, -0.0848999, -0.075683594, -0.06741333, -0.059387207, -0.051635742, -0.043182373, -0.03265381, -0.023223877, -0.012634277, -0.0018310547, 0.008361816, 0.020050049, 0.03137207, 0.04333496, 0.054626465, 0.06491089, 0.07601929, 0.086120605, 0.09609985, 0.106903076, 0.11764526, 0.12930298, 0.13845825, 0.14813232, 0.15621948, 0.1605835, 0.16403198, 0.16687012, 0.17114258, 0.1730957, 0.17614746, 0.17871094, 0.18014526, 0.18255615, 0.18405151, 0.18432617, 0.18380737, 0.18035889, 0.17684937, 0.17364502, 0.16931152, 0.16543579, 0.15917969, 0.1550293, 0.15100098, 0.14538574, 0.13903809, 0.13186646, 0.124176025, 0.11621094, 0.107421875, 0.09933472, 0.09057617, 0.08114624, 0.07342529, 0.06375122, 0.05606079, 0.044647217, 0.035186768, 0.026367188, 0.015777588, 0.0058898926, -0.006225586, -0.017608643, -0.028045654, -0.03994751, -0.05117798, -0.061401367, -0.07183838, -0.08270264, -0.09378052, -0.10372925, -0.1149292, -0.12451172, -0.13534546, -0.14328003, -0.15109253, -0.15524292, -0.15710449, -0.1614685, -0.16485596, -0.16925049, -0.1713562, -0.1737976, -0.17575073, -0.17715454, -0.17999268, -0.17959595, -0.17749023, -0.1743164, -0.17041016, -0.16705322, -0.1642456, -0.15930176, -0.15341187, -0.14697266, -0.14291382, -0.13760376, -0.13171387, -0.12652588, -0.118255615, -0.110687256, -0.10241699, -0.09259033, -0.082611084, -0.07388306, -0.06500244, -0.05657959, -0.048217773, -0.03881836, -0.028076172, -0.016662598, -0.007080078, 0.003692627, 0.014831543, 0.025817871, 0.039001465, 0.04949951, 0.06097412, 0.071746826, 0.08206177, 0.09378052, 0.10467529, 0.115600586, 0.12643433, 0.13705444, 0.14758301, 0.15576172, 0.16143799, 0.16635132, 0.16879272, 0.17337036, 0.17599487, 0.17770386, 0.17993164, 0.18157959, 0.18191528, 0.18566895, 0.18762207, 0.18588257, 0.18377686, 0.1795044, 0.17626953, 0.17276001, 0.16906738, 0.16311646, 0.15835571, 0.15222168, 0.14718628, 0.14193726, 0.13516235, 0.12783813, 0.12017822, 0.11126709, 0.102264404, 0.09439087, 0.084350586, 0.075408936, 0.06744385, 0.05960083, 0.050231934, 0.039764404, 0.030731201, 0.021209717, 0.009857178, -0.00061035156, -0.012176514, -0.023498535, -0.03463745, -0.04562378, -0.05596924, -0.06628418, -0.076812744, -0.0869751, -0.097351074, -0.108673096, -0.11871338, -0.12884521, -0.13796997, -0.14706421, -0.15185547, -0.15490723, -0.15829468, -0.1630249, -0.16625977, -0.16833496, -0.17150879, -0.17236328, -0.17416382, -0.17581177, -0.17807007, -0.17706299, -0.17507935, -0.17114258, -0.16775513, -0.16455078, -0.1600647, -0.15597534, -0.15002441, -0.14501953, -0.13943481, -0.13421631, -0.12768555, -0.12158203, -0.11566162, -0.10714722, -0.09906006, -0.08831787, -0.07949829, -0.070892334, -0.06265259, -0.055664062, -0.046325684, -0.036315918, -0.026184082, -0.016326904, -0.0053100586, 0.0052490234, 0.015686035, 0.028137207, 0.039733887, 0.049987793, 0.060913086, 0.071746826, 0.08300781, 0.093322754, 0.10360718, 0.11428833, 0.12435913, 0.13446045, 0.14508057, 0.15258789, 0.15927124, 0.1633606, 0.16644287, 0.16976929, 0.17327881, 0.17510986, 0.17694092, 0.17733765, 0.18081665, 0.18289185, 0.18383789, 0.18383789, 0.18035889, 0.17834473, 0.17434692, 0.1703186, 0.16467285, 0.16079712, 0.15527344, 0.15029907, 0.14501953, 0.14019775, 0.1335144, 0.12539673, 0.11785889, 0.108795166]
    signal_span = np.linspace(0, len(signal), len(signal))
    plt.plot(signal, label="Original signal")

    signal_fft = np.fft.fft(signal)
    print(signal_fft.shape)
    signal_fft_power = np.abs(signal_fft)/len(signal)
    print(signal_fft_power.shape)

    print(f"Highest harmonics: {get_highest_harmonics(signal_fft_power)}")
    reconstructed_signal = reconstruct_signal_based_on_harmonics(signal_fft_power, signal_span)
    print(reconstructed_signal.shape)
    plt.plot(reconstructed_signal, '-', label="reconstructed signal")
    plt.legend()
    plt.show()

