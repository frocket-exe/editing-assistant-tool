import subprocess
import matplotlib.pyplot as plt
import numpy as np
import wave, sys
import pandas as pd

def visualize(path):

    audioPath = "silent_video_segments/analysis.wav"
    cmd = ["ffmpeg", "-y", "-i", path, "-ab", "160k", "-ac", "2", "-ar", "44100", "-vn", audioPath]
    subprocess.run(cmd)
  
    raw = wave.open(audioPath)
    
    signal = raw.readframes(-1)
    signal = np.frombuffer(signal, dtype ="int16")
    
    f_rate = raw.getframerate()

    time = np.linspace(
        0,
        len(signal) / f_rate,
        num = len(signal)
    )

    df = pd.DataFrame(signal, time)
    return df