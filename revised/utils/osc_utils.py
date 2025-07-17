import pdb
import time
import random
from pythonosc import udp_client

# ----------------------------------------
# 🎼 스케일 정의
# ----------------------------------------
SCALES = {
    "C Pentatonic": [60, 62, 64, 67, 69],
    "C Major": [60, 62, 64, 65, 67, 69, 71],
    "C Minor": [60, 62, 63, 65, 67, 68, 70],
    "Chromatic": list(range(60, 72)),
}

def get_scale_notes(scale_name="C Pentatonic", base_octave=4, num_octaves=4):
    """
    주어진 스케일 이름과 옥타브 수에 따라 전체 MIDI 노트 리스트를 생성합니다.
    """
    if scale_name not in SCALES:
        print(f"⚠️ 경고: '{scale_name}' 스케일을 찾을 수 없습니다. C Pentatonic으로 대체합니다.")
        scale_name = "C Pentatonic"

    base_notes = SCALES[scale_name]
    all_notes = []
    
    # 기준 옥타브 아래로 확장
    for i in range(base_octave, 0, -1):
        notes = [note - (12 * (base_octave - i + 1)) for note in base_notes]
        all_notes.extend(notes)

    # 기준 옥타브부터 위로 확장
    for i in range(num_octaves):
        notes = [note + (12 * i) for note in base_notes]
        all_notes.extend(notes)
        
    # 중복 제거 및 정렬 후 0~127 범위 필터링
    final_notes = sorted(list(set(n for n in all_notes if 0 <= n <= 127)))
    return final_notes

# ----------------------------------------

def init_client(port, ip="127.0.0.1"):
    return udp_client.SimpleUDPClient(ip, port)


def send_midi(client, n_pieces, midi_data, vel_data, dur_data):
    N = random.randint(1, n_pieces)
    client.send_message("/note", random.sample(midi_data, N))
    client.send_message("/velocity", random.sample(vel_data, N))
    client.send_message("/duration", random.sample(dur_data, N))


def send_midi_td(client, n_pieces, midi_data, vel_data, dur_data):
    # 몇개의 노트를 연주할지 정하기.
    n_notes = random.randint(1, n_pieces)
    N = [random.randint(0, len(midi_data)-1) for i in range(n_notes)]
    midi_values, vel_values, dur_values = [], [], []
    for idx in N:
        midi_values.append(midi_data[idx])
        vel_values.append(vel_data[midi_data[idx]-21])
        dur_values.append(dur_data[midi_data[idx]-21])

    # midi = list(range(88))
    # vel = [0]*88
    # dur = [0]*88

    # for m, v, d in zip(midi_values, vel_values, dur_values):
    #     midi[m], vel[m], dur[m] = m, v, d

    client.send_message("/note", midi_values)
    client.send_message("/velocity", vel_values)
    client.send_message("/duration", dur_values)