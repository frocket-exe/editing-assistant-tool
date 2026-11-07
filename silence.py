from silero_vad import load_silero_vad, read_audio, get_speech_timestamps
import subprocess
import json

# Script options
mediaFolder = "media/"
inputName = "testVideo.mp4"
audioName = "extractedAudio.wav"
inputPath = mediaFolder + inputName
audioPath = mediaFolder + audioName
SAMPLE_RATE = 16000

# Convert input file to wav file for processing
cmd = ["ffmpeg", "-y", "-i", inputPath, "-q:a", "0", "-map", "a", audioPath]
subprocess.run(cmd)

# Get video duration from ffprobe
cmd = ["ffprobe", "-v", "quiet", "-print_format", "json", "-show_format", "-show_streams", audioPath]
result = subprocess.run(cmd, capture_output=True, text=True).stdout
duration = round(float(json.loads(result)["streams"][0]["duration"]), 2)

#Load model from local silero for offline use
model = load_silero_vad()
wav = read_audio(audioPath, sampling_rate=SAMPLE_RATE)

#Get timestamps of all spoken segctions of the audio
speechTimestamps = get_speech_timestamps(wav, model, sampling_rate=SAMPLE_RATE, threshold=0.5, min_speech_duration_ms=250, min_silence_duration_ms=100, return_seconds=True)
print(speechTimestamps)

#Use speaking segments to find silent segments
speechTimestamps.insert(0, {'end': 0.0})
speechTimestamps.append({'start': duration})
silentTimestamps = []
for i in range(len(speechTimestamps)-1):
    silentStart = speechTimestamps[i]['end']
    silendEnd = speechTimestamps[i+1]['start']
    silentSegment = {'start': silentStart, 'end': silendEnd, 'duration': silendEnd-silentStart}
    silentTimestamps.append(silentSegment)
print(silentTimestamps)