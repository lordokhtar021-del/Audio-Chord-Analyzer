from typing import TypedDict, Optional
import datetime


class Project(TypedDict):
    id: int
    name: str
    created_at: datetime.datetime


class Track(TypedDict):
    id: int
    project_id: Optional[int]
    filename: str
    original_filename: str
    duration: float
    created_at: datetime.datetime


class Analysis(TypedDict):
    id: int
    track_id: Optional[int]
    status: str
    progress: int
    tempo: float
    key: str
    created_at: datetime.datetime


class Chord(TypedDict):
    id: int
    analysis_id: Optional[int]
    start_time: float
    end_time: float
    chord_name: str
    confidence: float


class AnalysisResult(TypedDict):
    tempo: float
    key: str
    chords: list[dict[str, str | float]]