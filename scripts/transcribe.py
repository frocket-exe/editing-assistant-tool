import whisperx

def transcribe(filePath):
    print("Transcribing....")
    modelSize = "large-v2"
    device = "cpu"
    compute_type = "int8"
    model = whisperx.load_model(modelSize, device, compute_type=compute_type)
    audio = whisperx.load_audio(filePath)
    transcription = model.transcribe(audio, language="en")
    print(transcription["segments"])

transcribe("media/testVideo.mp4")