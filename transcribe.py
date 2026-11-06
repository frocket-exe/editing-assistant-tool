import whisperx

def transcribe(filePath):
    print("Transcribing....")
    modelSize = "base"
    device = "cpu"
    compute_type = "int8"
    model = whisperx.load_model(modelSize, device, compute_type)
    transcription = model.transcribe(filePath)
    print(transcription)

transcribe("./media/testAudio.mp3")