import whisperx

# Transcribes a given video/audio file based on it's path
# using WhisperX, an open source local AI transcription model
def transcribe(filePath):
    print("Transcribing....")
    modelSize = "large-v2"
    device = "cpu"
    compute_type = "int8"
    model = whisperx.load_model(modelSize, device, compute_type=compute_type)
    audio = whisperx.load_audio(filePath)
    transcription = model.transcribe(audio, language="en")
    return transcription['segments']

# Converts seconds to the timecode format used in the srt standard
def secondsToTimecode(seconds):
    hours = int(seconds // 3600)
    mins = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    milliseconds = int((seconds * 1000) % 1000)
    return(f"{hours:02}:{mins:02}:{secs:02},{milliseconds:03}")

# Converts a transcription from the model into an srt file to be used for subtitles
def transcriptionToSrt(transcription):
    srtText = ""
    for i, segment in enumerate(transcription):
        srtText += f"{i+1}\n"
        srtText += f"{secondsToTimecode(segment["start"])} --> {secondsToTimecode(segment["end"])}\n"
        srtText += segment["text"]
    with open("srt/transcription.srt", "w") as f:
        f.write(srtText)
        f.close()

t = transcribe("media/testVideo.mp4")
transcriptionToSrt(t)