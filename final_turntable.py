import os
os.environ["OPENCV_VIDEOIO_MSMF_ENABLE_HW_TRANSFORMS"] = "0"
import pdb
import time
import random
import cv2 as cv
import numpy as np
import pandas as pd

from utils.audio_utils import select_scale, ValMapper
from utils.osc_utils import init_client, send_midi, send_midi_td

import argparse
parser = argparse.ArgumentParser(description='')
# parser.add_argument('-v', '--video', type=str, default='video.mp4')
parser.add_argument('-r', '--manual_roi', type=str, default='y', help='y/n')
parser.add_argument('--pad', type=int, default=1)
parser.add_argument('-s', '--scale', type=str, default='CPentatonic', help='piano, CMajor, CPentatonic, CLydian, etc.')
parser.add_argument('-b', '--tempo', type=int, default=60)
parser.add_argument('-t', '--threshold', type=int, default=0)
parser.add_argument('--skip', type=int, default=90, help='frame skip rate')
parser.add_argument('--mode', type=str, default='linear')
parser.add_argument('--vel_min', type=int, default=32.0)
parser.add_argument('--vel_max', type=int, default=127.0)
parser.add_argument('--dur_min', type=float, default=0.8)
parser.add_argument('--dur_max', type=float, default=1.8)
args = parser.parse_args()


note_midis = select_scale(args.scale)
num_notes = len(note_midis)
zodiac_range = 88
time_per_beat = round(1 / args.tempo, 4) # [ms]

### camera intrinsic parameters ###
fps = 60

cap = cv.VideoCapture(1)
# cap.set(cv.CAP_PROP_FRAME_WIDTH, 1920)
# cap.set(cv.CAP_PROP_FRAME_WIDTH, 1080)
cap.set(cv.CAP_PROP_FRAME_WIDTH, 3000)
cap.set(cv.CAP_PROP_FRAME_WIDTH, 3000)

# frame_status = a boolean return value from getting the frame
# first_frame = the first frame in the entire video sequence
frame_status, first_frame = cap.read()
# vertical
first_frame = cv.rotate(first_frame, cv.ROTATE_90_CLOCKWISE)
print("Video size in pixel: ", first_frame.shape)
# get xlen & ylen of frame
xlen = first_frame.shape[1]
ylen = first_frame.shape[0]

# if args.manual_roi == 'y':  # Use manual ROI
#     x, y, w, h = cv.selectROI('mouse', first_frame, False)
#     print(f"ROI box: x: {x}, y: {y}, w: {w}, h: {h}")
#     h_x, h_y = y, xlen-x
#     print(f"ROI box: h_x: {h_x}, h_y: {h_y}")
# specify your scale percent, for example 50% of original size
scale_percent = 20 

# calculate the new dimensions
width = int(first_frame.shape[1] * scale_percent / 100)
height = int(first_frame.shape[0] * scale_percent / 100)

# create a tuple of new dimensions
dim = (width, height)

# resize image
resized_frame = cv.resize(first_frame, dim, interpolation = cv.INTER_AREA)

if args.manual_roi == 'y':  # Use manual ROI
    x, y, w, h = cv.selectROI('mouse', resized_frame, False)
    
    # Scale the ROI coordinates back to original image size
    x = int(x / (scale_percent/100))
    y = int(y / (scale_percent/100))
    w = int(w / (scale_percent/100))
    h = int(h / (scale_percent/100))
    
    print(f"ROI box: x: {x}, y: {y}, w: {w}, h: {h}")
    h_x, h_y = y, xlen-x
    print(f"ROI box: h_x: {h_x}, h_y: {h_y}")

else: # ?
    x, y, w = first_frame.shape[0] // 2, 50, 0
    h = 88*5 if first_frame.shape[1] < 2000 else 88*10

# control
cv.waitKey(1)
cv.destroyWindow('mouse')
cv.destroyAllWindows()
cv.waitKey(1)

# num_area = (h // num_notes) if (h % num_notes == 0) else (h // num_notes + 1)
n_tgt_area = h // num_notes
n_res_area = h % num_notes
# n_tgt_area = w // num_notes
# n_res_area = w % num_notes

client_5555 = init_client(port=5555)
client_5556 = init_client(port=5556)
frame_count = 0
frame_skip_rate = args.skip
# frame_skip_rate = random.randint(10, 30)
pixel_threshold = args.threshold

### Visualization ###
screen_width = h // 10
flattened_roi = np.zeros((screen_width, int(h), 3)).astype(np.uint8)
zodiac_flattened_roi = np.zeros((screen_width, int(zodiac_range), 3)).astype(np.uint8)

### zodiac ###
twFlag = True
if(twFlag):
    n_tgt_area = 1
    # hour_frame = 30 * 60 * 10   # 10 minutes per 1 zodiac hour
    time_per_zodiac_area = 30
    hour_frame = fps * time_per_zodiac_area # 원하는 초
    hour_cnt = 0
cnt = 0
while(True):
    start = time.time()
    ret, frame = cap.read()
    # use horizontal frame for visualization
    horizontal_frame = frame
    # use vertical frame for sound processing
    vertical_frame = cv.rotate(frame, cv.ROTATE_90_CLOCKWISE)   
    # print(ret)
    if not ret:
        print('video error')
        cv.waitKey(1)
        cv.destroyAllWindows()
        cv.waitKey(1)
        break

    # zodiac
    if(twFlag):
        if(h < zodiac_range * 12):
            print("h is too small for zodiac")
            break
        if(hour_cnt >= 12):
            print("reached 12 hours")
            break
        hour_cnt = frame_count // hour_frame
        # new range: zodiac_h:zodiac_h+num_notes 
        zodiac_h_x = h_x + zodiac_range * hour_cnt
        zodiac_h = y + zodiac_range * hour_cnt
        # print(f"frame_cnt: {frame_count}, hour_cnt: {hour_cnt}")
        # print(f"zodiac_h_x: {h_x}, zodiac_h: {zodiac_h}")

    roi = vertical_frame[y:y+h, x:x+args.pad]
    if(twFlag):
        zodiac_roi = vertical_frame[zodiac_h:zodiac_h+zodiac_range, x:x+args.pad]
        roi_gray = cv.cvtColor(zodiac_roi, cv.COLOR_BGR2GRAY)
    else:
        roi_gray = cv.cvtColor(roi, cv.COLOR_BGR2GRAY)
    cv.imshow('ROI', roi)

    ### Visualization ###
    # flattened_roi = np.zeros((h, 1000, 3)).astype(np.uint8)
    # print( horizontal_frame[h_y:h_y+1, h_x: h_x+h, :])
    # cv.imshow( horizontal_frame[h_y:h_y+1, h_x: h_x+h, :])
    flattened_roi = np.delete(flattened_roi, 0, axis = 0)
    flattened_roi = np.insert(flattened_roi, -1, horizontal_frame[h_y:h_y+1, h_x: h_x+h, :].astype(np.uint8), axis = 0)
    cnt += 1
    print(cnt)
    # print(num_notes)
    if(twFlag):
        zodiac_flattened_roi = np.delete(zodiac_flattened_roi, 0, axis = 0)
        zodiac_flattened_roi = np.insert(zodiac_flattened_roi, -1, horizontal_frame[h_y:h_y+1, zodiac_h_x: zodiac_h_x+zodiac_range, :].astype(np.uint8), axis = 0)

    rotated_flattened_roi = cv.rotate(flattened_roi, cv.ROTATE_90_CLOCKWISE)
    scaled_rotated_flattened_roi = cv.resize(rotated_flattened_roi, (10000,3000))
    cv.imshow("scaled_rotated_flattened_roi", scaled_rotated_flattened_roi)
    if(twFlag):
        rotated_zodiac_flattened_roi = cv.rotate(zodiac_flattened_roi, cv.ROTATE_90_CLOCKWISE)
        cv.imshow("zodiac_flattened_roi", rotated_zodiac_flattened_roi)

    if(twFlag):
        if frame_count % frame_skip_rate == 0:
            start = time.time()
            data = []
            for one_note in range(zodiac_range):
                note_start = one_note*n_tgt_area
                note_end = (one_note+1)*n_tgt_area
                magnitude = np.mean(roi_gray[note_start:note_end, :], axis=0)
                data.append({'frame_num': frame_count, 'magnitude': magnitude})

            df_gray_values = pd.DataFrame(data)
            frame_nums = df_gray_values['frame_num'].values
            magnitudes = df_gray_values['magnitude'].values

            # midi_data = [note_midis[i % num_notes] for i in range(df_gray_values.shape[0])]
            midi_data = note_midis

            # Convert magnitude to velocity and duration
            mag2vel = ValMapper('linear', magnitudes, min(magnitudes), max(magnitudes), args.vel_min, args.vel_max)
            # get random integer from -20 to 20
            light_bound = 20
            lightness = np.random.randint(-light_bound, light_bound, len(magnitudes))
            lighted_magnitudes = magnitudes + lightness
            mag2dur = ValMapper('linear', lighted_magnitudes, min(lighted_magnitudes), max(lighted_magnitudes), args.dur_min, args.dur_max)
            vel_data, dur_data = mag2vel(), mag2dur() #normalize data from 0 to 1 

            vel_data = [round(i.item(), 1)for i in vel_data]
            dur_data = [round(i.item(), 1)for i in dur_data]
            # print(f"midi: {len(midi_data)}, vel: {len(vel_data)}, dur: {len(dur_data)}")

            n_east = 5
            # send_midi(client_5555, n_east, midi_data, vel_data, dur_data)  # east
            send_midi_td(client_5555, n_east, midi_data, vel_data, dur_data)

            n_west = 1
            # send_midi(client_5556, n_west, midi_data, vel_data, dur_data)  # west
            send_midi_td(client_5556, n_west, midi_data, vel_data, dur_data)  # east
            print(f'==={cnt}===')
            # time.sleep(1)

    else:
        # print("not zodiac")
        start_index = n_res_area // 2
        end_index = h - (n_res_area - start_index)
        roi_gray = roi_gray[start_index:end_index, :]
        # assert (end_index - start_index) == (n_tgt_area * num_notes) 
        # Get pixel value of each row: saved in list(magnitude)
        if frame_count % frame_skip_rate == 0:
            start = time.time()
            data = []
            for one_note in range(num_notes):
                note_start = one_note*n_tgt_area
                note_end = (one_note+1)*n_tgt_area
                magnitude = np.mean(roi_gray[note_start:note_end, :], axis=0)
                data.append({'frame_num': frame_count, 'magnitude': magnitude})

            df_gray_values = pd.DataFrame(data)
            frame_nums = df_gray_values['frame_num'].values
            magnitudes = df_gray_values['magnitude'].values

            midi_data = [note_midis[i % num_notes] for i in range(df_gray_values.shape[0])]
            # Convert magnitude to velocity and duration
            mag2vel = ValMapper('linear', magnitudes, min(magnitudes), max(magnitudes), args.vel_min, args.vel_max)
            mag2dur = ValMapper('linear', magnitudes, min(magnitudes), max(magnitudes), args.dur_min, args.dur_max)
            vel_data, dur_data = mag2vel(), mag2dur() #normalize data from 0 to 1 
            # pdb.set_trace()
            assert len(midi_data) == len(vel_data) == len(dur_data)
            vel_data = [round(i.item(), 1)for i in vel_data]
            dur_data = [round(i.item(), 1)for i in dur_data]
            # print(f"midi: {len(midi_data)}, vel: {len(vel_data)}, dur: {len(dur_data)}")
            """ Process above takes 0.02 second. """
            split_send = 5

            send_midi(client_5555, split_send, midi_data, vel_data, dur_data)
    if cv.waitKey(1) & 0xff == ord('q'):
        break
    frame_count += 1



cv.destroyAllWindows()
cv.waitKey(1)
# The following frees up resources and closes all windows
cap.release()
cv.destroyAllWindows()