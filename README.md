# editing-assistant-tool

## The plan is simple...:
### High priority:
- [x] Import a video/audio
- [x] Display the properties of the video
- [x] Detect silence and add to EDL
- [X] Transcribe using whisperX
- [X] Export subtitles as SRT
- [X] Swear word detection (+ EDL)
- [X] Key word detection (+ EDL)
- [ ] Export media with choice of output quality

---

### Medium priority:
- [X] Mute swear words
- [X] Beep swear words
- [ ] Burn subtitles into video
- [ ] Normalise audio
- [ ] Estimate file output size
- [ ] Detect black frames

---

### Low priority:
- [ ] Compress audio
- [ ] Detect low-motion/static scenes
- [x] Auto cut silences
- [ ] Subtitle translation
- [ ] Plot graphs about video properties
- [ ] Compare score for video before/after processing

# Dependencies
- requirements.txt
- ffmpeg
- python 3.12

# Dummy don't forget these commands
+ .venv/Script/activate
+ pip freeze > requirements.txt
+ pip install -r requirements.txt

# AI Usage
### WhisperX local transcription/alignment model used
### Silero-VAD local voice activity detection model used