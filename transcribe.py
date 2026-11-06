import whisperx

def transcribe(filePath):
    print("Transcribing....")
    modelSize = "large-v2"
    device = "cpu"
    compute_type = "int8"
    model = whisperx.load_model(modelSize, device, compute_type=compute_type)
    transcription = model.transcribe(filePath, language="en")
    print(transcription["segments"])

transcribe("media/testAudio.wav")