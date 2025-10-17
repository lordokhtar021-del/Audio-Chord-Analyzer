import reflex as rx
from .state import State


def header() -> rx.Component:
    return rx.el.header(
        rx.el.div(
            rx.el.div(
                rx.icon(tag="git-branch-plus", class_name="text-violet-500"),
                rx.el.h1(
                    "Chord Analyzer", class_name="text-xl font-bold text-gray-800"
                ),
                class_name="flex items-center gap-3",
            ),
            rx.el.div(
                rx.el.a(
                    "Source Code",
                    href="https://github.com/reflex-dev/reflex",
                    target="_blank",
                    class_name="text-sm font-medium text-gray-600 hover:text-violet-600 transition-colors",
                ),
                class_name="flex items-center gap-4",
            ),
            class_name="container mx-auto flex justify-between items-center px-4 py-3",
        ),
        class_name="bg-white/80 backdrop-blur-sm border-b border-gray-200/80 sticky top-0 z-40",
    )


def upload_component() -> rx.Component:
    return rx.el.div(
        rx.upload.root(
            rx.el.div(
                rx.el.div(
                    rx.icon("cloud_upload", class_name="text-violet-500", size=32),
                    rx.el.h3(
                        "Click or drag and drop to upload",
                        class_name="font-semibold text-gray-700 mt-4",
                    ),
                    rx.el.p(
                        "Supports: MP3, WAV, FLAC, OGG, M4A",
                        class_name="text-sm text-gray-500 mt-1",
                    ),
                    class_name="text-center",
                ),
                class_name="flex flex-col items-center justify-center p-8 border-2 border-dashed border-gray-300 rounded-xl hover:border-violet-400 transition-colors duration-300 cursor-pointer bg-gray-50/50",
            ),
            id="upload_audio",
            on_drop=State.handle_upload,
            class_name="w-full max-w-lg",
            border="0px",
            padding="0px",
        ),
        class_name="w-full flex justify-center",
    )


def progress_bar(value: rx.Var[int], text: rx.Var[str]) -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.p(text, class_name="text-sm font-medium text-gray-600"),
            rx.el.p(f"{value}%", class_name="text-sm font-semibold text-violet-600"),
            class_name="flex justify-between mb-1",
        ),
        rx.el.div(
            rx.el.div(
                class_name="bg-violet-500 h-2 rounded-full transition-all duration-300",
                style={"width": value.to_string() + "%"},
            ),
            class_name="w-full bg-gray-200 rounded-full h-2",
        ),
    )


def analysis_view() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.h3(
                "Analyzing Audio", class_name="text-lg font-semibold text-gray-800"
            ),
            rx.el.p(
                State.uploaded_filename, class_name="text-sm text-gray-500 truncate"
            ),
            class_name="mb-4",
        ),
        progress_bar(State.analysis_progress, State.analysis_stage),
        class_name="w-full max-w-lg p-6 bg-white rounded-xl border border-gray-200 shadow-sm",
    )


def upload_view() -> rx.Component:
    return rx.el.div(
        rx.el.h2(
            "Upload Your Audio File", class_name="text-2xl font-bold text-gray-800 mb-2"
        ),
        rx.el.p(
            "Get instant chord progression analysis for your songs.",
            class_name="text-gray-600 mb-8",
        ),
        upload_component(),
        rx.cond(
            State.error_message != "",
            rx.el.div(
                rx.icon("flag_triangle_right", class_name="text-red-500 mr-2"),
                rx.el.p(
                    State.error_message, class_name="text-red-600 text-sm font-medium"
                ),
                class_name="mt-4 flex items-center bg-red-50 p-3 rounded-lg border border-red-200",
            ),
        ),
        class_name="flex flex-col items-center justify-center text-center",
    )


def uploading_view() -> rx.Component:
    return rx.el.div(
        rx.el.h3("Uploading...", class_name="text-lg font-semibold text-gray-800 mb-4"),
        progress_bar(State.upload_progress, rx.Var.create("Uploading file")),
        class_name="w-full max-w-lg p-6 bg-white rounded-xl border border-gray-200 shadow-sm",
    )


def waveform_view() -> rx.Component:
    return rx.el.div(
        rx.foreach(
            State.waveform_data,
            lambda point, i: rx.el.div(
                class_name="bg-violet-300 w-px rounded-full",
                style={"height": point * 100 + 1},
            ),
        ),
        class_name="flex items-center gap-px h-24 overflow-hidden",
    )


def timeline_chord_bar(chord: rx.Var, index: int, duration: rx.Var) -> rx.Component:
    left_pos = chord["start_time"].to(float) / duration.to(float) * 100
    width = (
        (chord["end_time"].to(float) - chord["start_time"].to(float))
        / duration.to(float)
        * 100
    )
    return rx.el.div(
        rx.el.p(chord["chord_name"], class_name="text-xs font-semibold truncate px-2"),
        class_name=rx.cond(
            State.selected_chord_index == index,
            "absolute h-full flex items-center bg-violet-400/50 border-2 border-violet-600 text-white rounded-md shadow-lg",
            "absolute h-full flex items-center bg-violet-200/50 text-violet-800 border border-violet-300 rounded-md hover:bg-violet-300/70",
        ),
        style={"left": left_pos.to_string() + "%", "width": width.to_string() + "%"},
        on_click=State.select_chord(index),
    )


def chord_timeline() -> rx.Component:
    return rx.el.div(
        rx.foreach(
            State.analysis_result["chords"],
            lambda chord, i: timeline_chord_bar(chord, i, State.audio_duration),
        ),
        class_name="relative w-full h-8 mt-2",
    )


def chord_editor(index: rx.Var, chord: rx.Var) -> rx.Component:
    return rx.el.form(
        rx.el.input(type="hidden", name="index", value=index),
        rx.el.input(
            name="chord_name",
            default_value=chord["chord_name"],
            class_name="font-mono w-full px-2 py-1 rounded border border-violet-400 bg-white",
        ),
        rx.el.div(
            rx.el.button(
                "Save",
                type="submit",
                class_name="text-xs bg-green-500 text-white px-2 py-1 rounded hover:bg-green-600",
            ),
            rx.el.button(
                "Cancel",
                on_click=State.cancel_edit_chord,
                type="button",
                class_name="text-xs bg-gray-200 px-2 py-1 rounded hover:bg-gray-300 ml-2",
            ),
            class_name="flex mt-2",
        ),
        on_submit=State.save_chord_edit,
        class_name="p-2 bg-violet-100 rounded-b-lg",
    )


def chord_info_panel() -> rx.Component:
    return rx.el.div(
        rx.cond(
            State.selected_chord.is_not_none(),
            rx.el.div(
                rx.el.div(
                    rx.el.div(
                        rx.el.p(
                            "Selected Chord",
                            class_name="text-sm text-gray-500 font-medium",
                        ),
                        rx.el.h4(
                            State.selected_chord["chord_name"],
                            class_name="text-2xl font-bold font-mono text-violet-600",
                        ),
                        class_name="flex-1",
                    ),
                    rx.el.div(
                        rx.el.button(
                            rx.icon(tag="disc_3", size=14),
                            on_click=State.set_editing_chord(
                                State.selected_chord_index
                            ),
                            class_name="p-2 text-gray-500 hover:text-violet-600 hover:bg-violet-100 rounded-md",
                        ),
                        rx.el.button(
                            rx.icon(tag="audio_lines", size=14),
                            class_name="p-2 text-gray-500 hover:text-violet-600 hover:bg-violet-100 rounded-md",
                        ),
                        class_name="flex items-center gap-1",
                    ),
                    class_name="flex justify-between items-start p-4",
                ),
                rx.cond(
                    State.editing_chord_index == State.selected_chord_index,
                    chord_editor(State.selected_chord_index, State.selected_chord),
                    rx.el.div(
                        rx.el.div(
                            rx.el.p("Confidence", class_name="text-xs text-gray-400"),
                            rx.el.p(
                                f"{(State.selected_chord['confidence'].to(float) * 100).to(int)}%",
                                class_name="font-semibold text-gray-700",
                            ),
                            class_name="px-4 pb-4",
                        ),
                        rx.el.div(
                            rx.el.p("Duration", class_name="text-xs text-gray-400"),
                            rx.el.p(
                                f"{State.selected_chord['end_time'].to(float) - State.selected_chord['start_time'].to(float):.2f}s",
                                class_name="font-semibold text-gray-700",
                            ),
                            class_name="px-4 pb-4",
                        ),
                    ),
                ),
            ),
            rx.el.div(
                rx.el.p(
                    "Click on a chord in the timeline to see details.",
                    class_name="text-sm text-gray-500",
                ),
                class_name="flex items-center justify-center h-full p-4",
            ),
        ),
        class_name="bg-white border border-gray-200 rounded-xl shadow-sm min-h-[120px]",
    )


def results_view() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.div(
                rx.el.div(
                    rx.el.h2(
                        "Analysis Results",
                        class_name="text-2xl font-bold text-gray-800",
                    ),
                    rx.el.p(
                        State.uploaded_filename.split("_")[-1],
                        class_name="text-gray-500 max-w-md truncate",
                    ),
                ),
                rx.el.div(
                    rx.el.button(
                        rx.icon(tag="cloud_download", class_name="mr-2", size=16),
                        "Export MIDI",
                        on_click=State.export_midi,
                        class_name="bg-gray-100 text-gray-700 px-4 py-2 rounded-lg hover:bg-gray-200 transition-colors flex items-center font-medium text-sm border border-gray-200",
                    ),
                    rx.el.button(
                        rx.icon(tag="rotate_cw", class_name="mr-2", size=16),
                        "Analyze New File",
                        on_click=State.reset_state,
                        class_name="bg-violet-500 text-white px-4 py-2 rounded-lg hover:bg-violet-600 transition-colors flex items-center font-medium text-sm shadow-sm",
                    ),
                    class_name="flex items-center gap-3",
                ),
                class_name="flex justify-between items-start mb-6",
            ),
            rx.el.div(
                waveform_view(),
                chord_timeline(),
                class_name="w-full p-4 bg-gray-100 rounded-xl border border-gray-200 shadow-inner",
            ),
            rx.el.div(
                rx.el.div(
                    rx.el.div(
                        rx.el.p(
                            "Tempo", class_name="text-sm font-medium text-gray-500"
                        ),
                        rx.el.p(
                            f"{State.analysis_result['tempo'].to(int)} BPM",
                            class_name="text-lg font-semibold text-violet-600",
                        ),
                        class_name="text-center p-4 bg-white rounded-xl border border-gray-200 shadow-sm",
                    ),
                    rx.el.div(
                        rx.el.p("Key", class_name="text-sm font-medium text-gray-500"),
                        rx.el.p(
                            State.analysis_result["key"],
                            class_name="text-lg font-semibold text-violet-600",
                        ),
                        class_name="text-center p-4 bg-white rounded-xl border border-gray-200 shadow-sm",
                    ),
                ),
                chord_info_panel(),
                class_name="mt-6 grid grid-cols-1 md:grid-cols-2 gap-6 items-start",
            ),
            class_name="w-full max-w-5xl mx-auto",
        ),
        class_name="w-full flex flex-col items-center justify-center p-8",
    )