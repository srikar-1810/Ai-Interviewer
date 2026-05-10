import io
import re
import librosa
import numpy as np


SAMPLE_RATE = 16000
FMIN = 65
FMAX = 2093
FRAME_LENGTH_MS = 25
HOP_LENGTH_MS = 10
VAD_ENERGY_THRESHOLD = 0.3
TARGET_SPEECH_RATE = 140


def _compute_vad(y: np.ndarray, sr: int) -> tuple[np.ndarray, float]:
    frame_length = int(sr * FRAME_LENGTH_MS / 1000)
    hop_length = int(sr * HOP_LENGTH_MS / 1000)
    energy = librosa.feature.rms(y=y, frame_length=frame_length, hop_length=hop_length)[0]
    threshold = np.mean(energy) * VAD_ENERGY_THRESHOLD
    is_voice = energy > threshold
    silence_ratio = float(1.0 - np.mean(is_voice))
    return is_voice, silence_ratio


def analyze_audio_bytes(audio_bytes: bytes, transcript: str = "") -> dict:
    y, sr = librosa.load(io.BytesIO(audio_bytes), sr=SAMPLE_RATE)
    duration = len(y) / sr

    pitch_variation = 0.0
    tone_stability = 50.0
    energy_stability = 50.0
    silence_ratio = 0.0
    speech_rate = 0
    f0_mean = 0.0

    if duration < 0.1:
        return _fallback(transcript, duration)

    f0, voiced_flag, _ = librosa.pyin(y, fmin=FMIN, fmax=FMAX, sr=sr)
    f0_voiced = f0[voiced_flag]
    if len(f0_voiced) > 0:
        f0_mean = float(np.mean(f0_voiced))
        pitch_variation = float(np.std(f0_voiced))

    spectral_centroids = librosa.feature.spectral_centroid(y=y, sr=sr)[0]
    sc_mean = float(np.mean(spectral_centroids)) if len(spectral_centroids) > 0 else 1
    sc_std = float(np.std(spectral_centroids)) if len(spectral_centroids) > 0 else 0
    tone_stability = max(0.0, 100.0 - (sc_std / max(sc_mean, 1)) * 100.0)

    rms = librosa.feature.rms(y=y)[0]
    rms_mean = float(np.mean(rms)) if len(rms) > 0 else 1
    rms_std = float(np.std(rms)) if len(rms) > 0 else 0
    energy_stability = max(0.0, 100.0 - (rms_std / max(rms_mean, 1)) * 100.0)

    is_voice, silence_ratio = _compute_vad(y, sr)

    word_count = len(transcript.split())
    speech_rate = int(word_count / max(duration / 60.0, 0.1))

    confidence_score = int(min(
        energy_stability * 0.35 +
        (100.0 - silence_ratio * 100.0) * 0.35 +
        max(0.0, 100.0 - abs(speech_rate - TARGET_SPEECH_RATE) * 0.5) * 0.3,
        99.0
    ))

    clarity_score = int(min(
        tone_stability * 0.4 +
        (100.0 - silence_ratio * 100.0) * 0.3 +
        max(0.0, 100.0 - abs(speech_rate - TARGET_SPEECH_RATE) * 0.4) * 0.2 +
        (min(pitch_variation, 50) / 50) * 10,
        99.0
    ))

    hesitation_score = int(min(
        silence_ratio * 100.0 + (speech_rate < 80) * 20.0,
        99.0
    ))

    return {
        "confidenceScore": max(confidence_score, 20),
        "communicationClarityScore": max(clarity_score, 20),
        "hesitationScore": hesitation_score,
        "pitchVariation": round(pitch_variation, 2),
        "f0Mean": round(f0_mean, 1),
        "toneStability": round(tone_stability, 1),
        "energyStability": round(energy_stability, 1),
        "silenceRatio": round(silence_ratio, 3),
        "speechRateWpm": speech_rate,
        "duration": round(duration, 2),
    }


def analyze_speech(transcript: str, duration_seconds: float = 60.0) -> dict:
    return _fallback(transcript, duration_seconds)


def _fallback(transcript: str, duration_seconds: float = 60.0) -> dict:
    words = transcript.split()
    word_count = len(words)
    sentences = [s.strip() for s in re.split(r'[.!?]+', transcript) if s.strip()]
    sentence_count = len(sentences)
    avg_words_per_sentence = word_count / max(sentence_count, 1)

    filler_words = {"um", "uh", "like", "you know", "sort of", "kind of", "actually", "basically", "i mean", "so"}
    filler_count = sum(1 for word in words if word.lower().strip(".,!?") in filler_words)
    filler_density = filler_count / max(word_count, 1)

    pauses = re.findall(r'\.{3,}|\s{2,}', transcript)
    avg_pause_duration = min(len(pauses) * 0.3, 3.0) if pauses else 0.0

    speech_rate = word_count / max(duration_seconds / 60.0, 1)
    fill_score = max(0, 100 - (filler_density * 500))
    rate_score = 100 - min(abs(speech_rate - TARGET_SPEECH_RATE) * 0.5, 50)
    confidence_score = int(min((fill_score * 0.5 + rate_score * 0.3 + 70 * 0.2), 99))

    clarity_score = int(min(
        100 - (filler_density * 300) - min(abs(avg_words_per_sentence - 15) * 2, 30),
        99
    ))
    clarity_score = max(clarity_score, 20)
    hesitation_score = int(min(filler_density * 500 + min(avg_pause_duration * 15, 30), 99))
    tone_variance = min(abs(speech_rate - 130) * 0.3 + 50, 95)

    return {
        "confidenceScore": max(confidence_score, 30),
        "communicationClarityScore": clarity_score,
        "hesitationScore": int(hesitation_score),
        "toneVariance": int(tone_variance),
        "fillerWordCount": filler_count,
        "speechRateWpm": int(speech_rate),
        "avgSentenceLength": round(avg_words_per_sentence, 1),
        "pitchVariation": 0.0,
        "toneStability": float(tone_variance),
        "energyStability": 50.0,
        "silenceRatio": round(avg_pause_duration / 10.0, 3),
    }
