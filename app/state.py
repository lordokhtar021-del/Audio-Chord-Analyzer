import reflex as rx
from typing import Literal, Any, cast
import asyncio
import time
import random
import string
import librosa
from . import analysis as audio_analysis
from .database import AnalysisResult

AnalysisStatus = Literal["idle", "uploading", "analyzing", "complete", "error"]
ALLOWED_EXTENSIONS = ["mp3", "wav", "flac", "ogg", "m4a"]


class State(rx.State):
    analysis_status: AnalysisStatus = "idle"
    upload_progress: int = 0
    uploaded_filename: str = ""
    error_message: str = ""
    analysis_progress: int = 0
    analysis_stage: str = ""
    analysis_result: AnalysisResult | None = None
    waveform_data: list[float] = []
    audio_duration: float = 0.0
    selected_chord_index: int = -1
    editing_chord_index: int = -1

    @rx.var
    def is_uploading(self) -> bool:
        return self.analysis_status == "uploading"

    @rx.var
    def is_analyzing(self) -> bool:
        return self.analysis_status == "analyzing"

    @rx.var
    def show_results(self) -> bool:
        return self.analysis_status == "complete"

    @rx.var
    def selected_chord(self) -> dict | None:
        if self.analysis_result and self.selected_chord_index != -1:
            return self.analysis_result["chords"][self.selected_chord_index]
        return None

    def _get_file_extension(self, filename: str) -> str:
        return filename.split(".")[-1].lower()

    @rx.event
    async def handle_upload(self, files: list[rx.UploadFile]):
        if not files:
            return
        upload_file = files[0]
        file_extension = self._get_file_extension(upload_file.name)
        if file_extension not in ALLOWED_EXTENSIONS:
            self.analysis_status = "error"
            self.error_message = f"Invalid file type. Please upload one of: {', '.join(ALLOWED_EXTENSIONS)}"
            return
        self.analysis_status = "uploading"
        self.error_message = ""
        self.uploaded_filename = upload_file.name
        upload_data = await upload_file.read()
        upload_dir = rx.get_upload_dir()
        upload_dir.mkdir(parents=True, exist_ok=True)
        unique_suffix = "".join(
            random.choices(string.ascii_letters + string.digits, k=8)
        )
        unique_name = f"{unique_suffix}_{upload_file.name}"
        file_path = upload_dir / unique_name
        total_size = len(upload_data)
        chunk_size = 1024 * 1024
        with file_path.open("wb") as f:
            for i in range(0, total_size, chunk_size):
                chunk = upload_data[i : i + chunk_size]
                f.write(chunk)
                progress = min(100, int((i + len(chunk)) / total_size * 100))
                self.upload_progress = progress
                yield
        self.analysis_status = "analyzing"
        self.uploaded_filename = unique_name
        yield State.start_analysis
        return

    @rx.event(background=True)
    async def start_analysis(self):
        file_path = rx.get_upload_dir() / self.uploaded_filename
        try:
            async with self:
                self.analysis_stage = "Loading Audio"
                self.analysis_progress = 5
            y, sr = audio_analysis.load_audio(file_path)
            async with self:
                self.analysis_stage = "Detecting Tempo & Beats"
                self.analysis_progress = 20
            yield
            await asyncio.sleep(0.1)
            tempo, beat_times = audio_analysis.detect_tempo_and_beats(y, sr)
            async with self:
                self.analysis_progress = 40
            yield
            async with self:
                self.analysis_stage = "Detecting Key"
                self.analysis_progress = 50
            yield
            await asyncio.sleep(0.1)
            key = audio_analysis.detect_key(y, sr)
            async with self:
                self.analysis_progress = 60
            yield
            async with self:
                self.analysis_stage = "Recognizing Chords"
                self.analysis_progress = 70
            yield
            await asyncio.sleep(0.1)
            chords = audio_analysis.recognize_chords(y, sr, beat_times)
            async with self:
                self.analysis_progress = 95
            yield
            waveform_data = audio_analysis.get_waveform_data(y)
            audio_duration = librosa.get_duration(y=y, sr=sr)
            async with self:
                self.analysis_stage = "Finalizing"
                self.analysis_result = {
                    "tempo": float(tempo),
                    "key": key,
                    "chords": chords,
                }
                self.waveform_data = waveform_data
                self.audio_duration = audio_duration
                self.analysis_progress = 100
                await asyncio.sleep(0.5)
                self.analysis_status = "complete"
        except Exception as e:
            import logging

            logging.exception(f"Analysis failed: {e}")
            async with self:
                self.analysis_status = "error"
                self.error_message = f"Analysis failed: {str(e)}"

    @rx.event
    def select_chord(self, index: int):
        self.selected_chord_index = index
        self.editing_chord_index = -1

    @rx.event
    def set_editing_chord(self, index: int):
        self.editing_chord_index = index

    @rx.event
    def cancel_edit_chord(self):
        self.editing_chord_index = -1

    @rx.event
    def save_chord_edit(self, form_data: dict):
        index = int(form_data.get("index", -1))
        new_name = form_data.get("chord_name", "").strip()
        if index != -1 and new_name and self.analysis_result:
            self.analysis_result["chords"][index]["chord_name"] = new_name
            self.analysis_result["chords"][index]["confidence"] = 1.0
        self.editing_chord_index = -1

    def _get_note_number(self, note_name: str) -> int:
        notes_map = {
            "C": 0,
            "C#": 1,
            "D": 2,
            "D#": 3,
            "E": 4,
            "F": 5,
            "F#": 6,
            "G": 7,
            "G#": 8,
            "A": 9,
            "A#": 10,
            "B": 11,
        }
        return notes_map.get(note_name.upper(), 60)

    @rx.event
    def export_midi(self) -> rx.event.EventSpec:
        if not self.analysis_result or not self.analysis_result["chords"]:
            return rx.toast("No chords to export.")
        import mido
        import io

        mid = mido.MidiFile(type=0)
        track = mido.MidiTrack()
        mid.tracks.append(track)
        ticks_per_beat = mid.ticks_per_beat
        tempo = self.analysis_result["tempo"]
        if tempo > 0:
            mido.bpm2tempo(tempo)
        last_event_time_ticks = 0
        for chord in self.analysis_result["chords"]:
            chord_name = chord["chord_name"]
            root_str = chord_name[0]
            if len(chord_name) > 1 and chord_name[1] == "#":
                root_str = chord_name[:2]
            root_note = self._get_note_number(root_str) + 60
            start_time_ticks = mido.second2tick(
                chord["start_time"], ticks_per_beat, mido.bpm2tempo(tempo)
            )
            end_time_ticks = mido.second2tick(
                chord["end_time"], ticks_per_beat, mido.bpm2tempo(tempo)
            )
            delta_on = int(start_time_ticks - last_event_time_ticks)
            delta_off = int(end_time_ticks - start_time_ticks)
            track.append(
                mido.Message("note_on", note=root_note, velocity=64, time=delta_on)
            )
            track.append(
                mido.Message("note_off", note=root_note, velocity=64, time=delta_off)
            )
            last_event_time_ticks = end_time_ticks
        midi_bytes = io.BytesIO()
        mid.save(file=midi_bytes)
        midi_bytes.seek(0)
        cleaned_filename = self.uploaded_filename.split("_", 1)[-1].rsplit(".", 1)[0]
        return rx.download(
            data=midi_bytes.read(), filename=f"{cleaned_filename}_chords.mid"
        )

    @rx.event
    def reset_state(self):
        self.analysis_status = "idle"
        self.upload_progress = 0
        self.uploaded_filename = ""
        self.error_message = ""
        self.analysis_progress = 0
        self.analysis_stage = ""
        self.analysis_result = None
        self.waveform_data = []
        self.audio_duration = 0.0
        self.selected_chord_index = -1
        self.editing_chord_index = -1