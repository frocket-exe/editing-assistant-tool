import whisperx

def transcribe(filePath):
    print("Transcribing....")
    model = whisperx.load_model("base")
    transcription = model.transcribe(filePath)
    print(transcription)

transcribe("./media/testAudio.mp3")