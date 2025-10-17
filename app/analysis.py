import librosa
import numpy as np
from typing import Any
from numpy.typing import NDArray as npndarray
import logging

SR = 22050
N_FFT = 2048
HOP_LENGTH = 512


def load_audio(file_path: str) -> tuple[np.ndarray, float]:
    try:
        y, sr = librosa.load(file_path, sr=SR, mono=True)
        return (y, sr)
    except Exception as e:
        logging.exception(f"Error loading audio file: {e}")
        raise IOError(f"Error loading audio file: {e}")


def get_waveform_data(y: np.ndarray, points: int = 500) -> list[float]:
    try:
        y_mono = y.mean(axis=0) if y.ndim > 1 else y
        samples_per_point = len(y_mono) // points
        if samples_per_point == 0:
            return []
        waveform = []
        for i in range(points):
            start = i * samples_per_point
            end = start + samples_per_point
            rms = np.sqrt(np.mean(y_mono[start:end] ** 2))
            waveform.append(float(rms))
        max_val = max(waveform) if waveform else 0
        if max_val > 0:
            waveform = [val / max_val for val in waveform]
        return waveform
    except Exception as e:
        logging.exception(f"Error generating waveform: {e}")
        return [0.0] * points


def detect_tempo_and_beats(y: np.ndarray, sr: float) -> tuple[float, np.ndarray]:
    tempo, beat_frames = librosa.beat.beat_track(y=y, sr=sr, hop_length=HOP_LENGTH)
    beat_times = librosa.frames_to_time(beat_frames, sr=sr, hop_length=HOP_LENGTH)
    return (tempo, beat_times)


KS_PROFILE = {
    "major": [6.35, 2.23, 3.48, 2.33, 4.38, 4.09, 2.52, 5.19, 2.39, 3.66, 2.29, 2.88],
    "minor": [6.33, 2.68, 3.52, 5.38, 2.6, 3.53, 2.54, 4.75, 3.98, 2.69, 3.34, 3.17],
}
NOTES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]


def detect_key(y: np.ndarray, sr: float) -> str:
    chroma = librosa.feature.chroma_stft(y=y, sr=sr)
    chroma_sum = np.sum(chroma, axis=1)
    correlations = []

    def get_correlation(item):
        return item[0]

    for i in range(12):
        for key_type in ["major", "minor"]:
            profile = np.roll(KS_PROFILE[key_type], i)
            correlation = np.corrcoef(chroma_sum, profile)[0, 1]
            correlations.append((correlation, f"{NOTES[i]} {key_type}"))
    best_fit = max(correlations, key=get_correlation) if correlations else (0, "N/A")
    return best_fit[1].capitalize()


def get_chord_templates() -> dict[str, np.ndarray]:
    templates = {}
    qualities = {
        "maj": [1, 0, 0, 0, 1, 0, 0, 1, 0, 0, 0, 0],
        "min": [1, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 0],
        "dim": [1, 0, 0, 1, 0, 0, 1, 0, 0, 0, 0, 0],
        "aug": [1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0],
        "sus2": [1, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0],
        "sus4": [1, 0, 0, 0, 0, 1, 0, 1, 0, 0, 0, 0],
        "7": [1, 0, 0, 0, 1, 0, 0, 1, 0, 0, 1, 0],
    }
    for root_i, root_name in enumerate(NOTES):
        for quality, pattern in qualities.items():
            rotated_pattern = np.roll(pattern, root_i)
            chord_name = f"{root_name}:{quality}"
            templates[chord_name] = rotated_pattern
    return templates


CHORD_TEMPLATES = get_chord_templates()


def _get_max_correlation_item(items):
    if not items:
        return (None, 0)

    def get_correlation_value(item):
        return item[1]

    return max(items, key=get_correlation_value)


def recognize_chords(
    y: npndarray, sr: float, beat_times: np.ndarray
) -> list[dict[str, float | str]]:
    chroma = librosa.feature.chroma_cqt(y=y, sr=sr)
    beat_frames = librosa.time_to_frames(beat_times, sr=sr)
    chords = []
    for i in range(len(beat_frames) - 1):
        start_frame, end_frame = (beat_frames[i], beat_frames[i + 1])
        if start_frame >= end_frame:
            continue
        segment_chroma = np.mean(chroma[:, start_frame:end_frame], axis=1)
        correlations = {}
        for chord_name, template in CHORD_TEMPLATES.items():
            correlation = np.corrcoef(segment_chroma, template)[0, 1]
            correlations[chord_name] = correlation
        best_chord, confidence = _get_max_correlation_item(correlations.items())
        if best_chord is None:
            continue
        start_time = librosa.frames_to_time(start_frame)
        end_time = librosa.frames_to_time(end_frame)
        chords.append(
            {
                "start_time": round(start_time, 2),
                "end_time": round(end_time, 2),
                "chord_name": best_chord.replace(":", ""),
                "confidence": round(float(confidence), 2),
            }
        )
    if not chords:
        return []
    merged_chords = [chords[0]]
    for i in range(1, len(chords)):
        if chords[i]["chord_name"] == merged_chords[-1]["chord_name"]:
            merged_chords[-1]["end_time"] = chords[i]["end_time"]
        else:
            merged_chords.append(chords[i])
    return merged_chords