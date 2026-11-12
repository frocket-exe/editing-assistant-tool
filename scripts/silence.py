from silero_vad import load_silero_vad, read_audio, get_speech_timestamps
import subprocess
import json
import os


def findSilences(inputPath):
    mediaFolder = "media/"
    audioName = "extractedAudio.wav"
    audioPath = mediaFolder + audioName
    SAMPLE_RATE = 16000

    # Convert input file to wav file for processing
    cmd = ["ffmpeg", "-y", "-i", inputPath, "-q:a", "0", "-map", "a", audioPath]
    subprocess.run(cmd)

    # Get video duration from ffprobe
    cmd = ["ffprobe", "-v", "quiet", "-print_format", "json", "-show_format", "-show_streams", audioPath]
    result = subprocess.run(cmd, capture_output=True, text=True).stdout
    duration = float(json.loads(result)["streams"][0]["duration"])

    cmd = ["ffprobe", "-v", "quiet", "-print_format", "json", "-show_format", "-show_streams", inputPath]
    result = subprocess.run(cmd, capture_output=True, text=True).stdout
    frameRate = int(json.loads(result)["streams"][0]["r_frame_rate"][:-2])

    #Load model from local silero for offline use
    model = load_silero_vad()
    wav = read_audio(audioPath, sampling_rate=SAMPLE_RATE)

    #Get timestamps of all spoken segctions of the audio
    speechTimestamps = get_speech_timestamps(wav, model, sampling_rate=SAMPLE_RATE, threshold=0.5, min_speech_duration_ms=250, min_silence_duration_ms=100, return_seconds=True)

    #Use speaking segments to find silent segments
    speechTimestamps.insert(0, {'end': 0.0})
    speechTimestamps.append({'start': duration})
    silentTimestamps = []
    for i in range(len(speechTimestamps)-1):
        silentStart = speechTimestamps[i]['end']
        silendEnd = speechTimestamps[i+1]['start']
        silentSegment = {'start': silentStart, 'end': silendEnd, 'duration': round(silendEnd-silentStart, 2)}
        silentTimestamps.append(silentSegment)

    # Writes to a json file to beuser by other functions
    json_silences = json.dumps(silentTimestamps, indent=4)
    with open("json/silences.json", "w") as f:
        f.write(json_silences)
        f.close()

    return frameRate

# Marks silences which are eligible to be cut based on user defined parameters:
# Minimum silence duration, attack and release
def markSilences(inputPath, minSilenceDuration, attack, release):
    frameRate = findSilences(inputPath)
    with open("json/silences.json", "r") as f:
        silences = json.load(f)
    cutSilences = []
    for i, silence in enumerate(silences):
        if silence["duration"] >= minSilenceDuration and silence["duration"] >= attack + release:
            if i != 0:
                cutSilenceStart = silence["start"] + release
            else:
                # Does not apply release if start of video is silent
                cutSilenceStart = silence["start"]
            if i != len(silences)-1:
                cutSilenceEnd = silence["end"] - attack
            else:
                # Does not apply attack if end of video is silent
                cutSilenceEnd = silence["end"]
            cutSilence = {'start': cutSilenceStart, 'end': cutSilenceEnd, 'note':'silence'}
            cutSilences.append(cutSilence)
    silences_data = {"title": "Silence to markers", "colour": "Red", "frameRate": frameRate, "timestamps": cutSilences}
    # Write to file
    json_silences = json.dumps(silences_data, indent=4)
    with open("json/silencesToCut.json", "w") as f:
        f.write(json_silences)
        f.close()
    return silences_data
        
def removeSilences(videoPath):
    # cmd = ["ffmpeg", "-y", "-i", videoPath, "-ss", "0.5", "-to", "3.5", "silent_video_segments/video_part01.mp4", "-ss", "5.4", "-to", "9", "silent_video_segments/video_part02.mp4"]
    cmd = ["ffmpeg", "-y", "-i", videoPath]
    with open("json/silencesToCut.json", "r") as f:
        silences_data = json.load(f)
    os.makedirs(os.path.dirname("silent_video_segments/segment_list.txt"), exist_ok=True)
    f = open("silent_video_segments/segment_list.txt", "w")
    silences = silences_data["timestamps"]
    silences.insert(0, {"end":0})
    for i in range(len(silences)-1):
        cmd.append("-ss")
        cmd.append(str(silences[i]["end"]))
        cmd.append("-to")
        cmd.append(str(silences[i+1]["start"]))
        # cmd.append("-c:v")
        # cmd.append("libx264")
        # cmd.append("-c:a")
        # cmd.append("aac")
        cmd.append(f"silent_video_segments/video_part{i:05}.mp4")
        f.write(f"file 'video_part{i:05}.mp4'\n")
    cmd.append("-ss")
    cmd.append(str(silences[(len(silences)-1)]["end"]))
    cmd.append("-t")
    cmd.append("99999")
    # cmd.append("-c:v")
    # cmd.append("libx264")
    # cmd.append("-c:a")
    # cmd.append("aac")
    cmd.append(f"silent_video_segments/video_part{(len(silences)-1):05}.mp4")
    f.write(f"file 'video_part{(len(silences)-1):05}.mp4'")
    f.close()
    subprocess.run(cmd)
    cmd = ["ffmpeg", "-y", "-fflags", "+genpts", "-f", "concat", "-i", "silent_video_segments/segment_list.txt", "-c", "copy", "media/cutVideo.mp4"]
    subprocess.run(cmd)

inputName = "testVideo.mp4"
inputPath = "media/" + inputName
# markSilences(inputPath, minSilenceDuration=1, attack=0.1, release=0.15)
removeSilences(inputPath)   