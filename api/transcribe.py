import os, wave, json
from vosk import Model, KaldiRecognizer

# path đến folder vosk-model-small-vn-0.4
MODEL_DIR = os.path.join(os.path.dirname(__file__), "vosk-model-small-vn-0.4")
if not os.path.isdir(MODEL_DIR):
    raise RuntimeError(f"Model not found at {MODEL_DIR}")

model = Model(MODEL_DIR)

def handler(request, response):
    # chỉ cho phép POST
    if request.method != "POST":
        return response.status(405).send("Method Not Allowed")

    audio = request.files.get("audio")
    if not audio:
        return response.status(400).json({"error": "Missing 'audio' file"})
    try:
        wf = wave.open(audio.stream, "rb")
    except wave.Error:
        return response.status(400).json({"error": "Invalid WAV file"})

    # kiểm tra mono 16kHz 16‑bit
    if wf.getnchannels()!=1 or wf.getsampwidth()!=2 or wf.getframerate()!=16000:
        return response.status(400).json({
            "error": (
                "Require WAV mono 16kHz 16‑bit. "
                f"Got channels={wf.getnchannels()}, "
                f"sampwidth={wf.getsampwidth()}, "
                f"framerate={wf.getframerate()}"
            )
        })

    rec = KaldiRecognizer(model, wf.getframerate())
    texts = []
    while True:
        data = wf.readframes(4000)
        if not data:
            break
        if rec.AcceptWaveform(data):
            part = json.loads(rec.Result())
            texts.append(part.get("text",""))
    final = json.loads(rec.FinalResult())
    texts.append(final.get("text",""))
    return response.json({"text": " ".join(t for t in texts if t)})
