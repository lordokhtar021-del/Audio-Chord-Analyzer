import reflex as rx
from .state import State
from .components import header, upload_view, uploading_view, analysis_view, results_view


def index() -> rx.Component:
    return rx.el.div(
        header(),
        rx.el.main(
            rx.el.div(
                rx.match(
                    State.analysis_status,
                    ("idle", upload_view()),
                    ("error", upload_view()),
                    ("uploading", uploading_view()),
                    ("analyzing", analysis_view()),
                    ("complete", results_view()),
                ),
                class_name="container mx-auto px-4 py-16 flex justify-center items-center",
            ),
            class_name="flex-grow",
        ),
        class_name="min-h-screen bg-gray-50 font-['Raleway'] flex flex-col",
    )


app = rx.App(
    theme=rx.theme(appearance="light"),
    head_components=[
        rx.el.link(rel="preconnect", href="https://fonts.googleapis.com"),
        rx.el.link(rel="preconnect", href="https://fonts.gstatic.com", cross_origin=""),
        rx.el.link(
            href="https://fonts.googleapis.com/css2?family=Raleway:wght@400;500;600;700&display=swap",
            rel="stylesheet",
        ),
    ],
)
app.add_page(index)