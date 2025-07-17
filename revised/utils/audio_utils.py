import math
from audiolazy import str2midi
import numpy as np


def select_scale(scale_selection="piano"):
    # TODO: change to dictionary
    # Option 1: using 100 consecutive notes
    if(scale_selection == "piano"):
        note_names = list(range(21, 21+88))
        isNoteStr = False
    # 4 octaves of major scale
    elif(scale_selection == 'CMajor'):
        note_names = ['C2','D2','E2','F2','G2','A2','B2',
                      'C3','D3','E3','F3','G3','A3','B3',
                      'C4','D4','E4','F4','G4','A4','B4',
                      'C5','D5','E5','F5','G5','A5','B5']
        isNoteStr = True
    #4 octaves of major pentatonic scale 
    elif(scale_selection == 'CPentatonic'):
        note_names = ['C2','D2','E2','G2','A2',
                      'C3','D3','E3','G3','A3',
                      'C4','D4','E4','G4','A4',
                      'C5','D5','E5','G5','A5']
        isNoteStr = True
    #custom note set (a voicing of a Cmaj13#11 chord, notes from C lydian)
    elif(scale_selection == 'CLydian'):
        note_names = ['C1','C2','G2',
                      'C3','E3','G3','A3','B3',
                      'D4','E4','G4','A4','B4',
                      'D5','E5','G5','A5','B5',
                      'D6','E6','F#6','G6','A6']
        isNoteStr = True
    elif(scale_selection == 'CWhole'): # 온음음계
        note_names = ['C2', 'D2', 'E2', 'F#2', 'G#2', 'A#2',
                      'C3', 'D3', 'E3', 'F#3', 'G#3', 'A#3',
                      'C4', 'D4', 'E4', 'F#4', 'G#4', 'A#4',
                      'C5', 'D5', 'E5', 'F#5', 'G#5', 'A#5'
                      ]
        isNoteStr = True

    else: 
        print("Please select available scale.")

    if(isNoteStr):
        note_midis = [str2midi(n) for n in note_names] #make a list of midi note numbers 
    else:
        note_midis = note_names

    return note_midis


class ValMapper:
    def __init__(self, 
                 mode: str, 
                 value: list, 
                 min_value: float, 
                 max_value: float, 
                 min_bound: float, 
                 max_bound: float):
        self.mode = mode
        self.value = value
        self.min_value = min_value
        self.max_value = max_value
        self.min_bound = min_bound
        self.max_bound = max_bound
        self.norm_scale = 1
        self.eps = 1e-7
    
    def norm(self):
        return [(v - self.min_value) / (self.max_value - self.min_value + self.eps) for v in self.value]

    def mapper(self):
        norm_values = self.norm()  # value between 0 and 1
        results = []
        
        for norm_value in norm_values:
            if self.mode == 'linear':
                result = norm_value
            elif self.mode == 'log':
                result = np.log(norm_value + self.eps)
            elif self.mode == 'power':
                result = np.power(norm_value, 2) # math.e
            elif self.mode == 'sin':
                result = np.sin(norm_value)
            else:
                raise ValueError(f"Invalid mode {self.mode}")
            
            results.append(self.min_bound + (self.max_bound - self.min_bound) * result)
        
        return results

    def __call__(self):
        return self.mapper()
