from django.urls import path

from . import bots_api_views

urlpatterns = [
    path("bots", bots_api_views.BotCreateView.as_view(), name="bot-create"),
    path(
        "bots/<str:object_id>",
        bots_api_views.BotDetailView.as_view(),
        name="bot-detail",
    ),
    path(
        "bots/<str:object_id>/leave",
        bots_api_views.BotLeaveView.as_view(),
        name="bot-leave",
    ),
    path(
        "bots/<str:object_id>/transcript",
        bots_api_views.TranscriptView.as_view(),
        name="bot-transcript",
    ),
    path(
        "bots/<str:object_id>/recording",
        bots_api_views.RecordingView.as_view(),
        name="bot-recording",
    ),
    path(
        "bots/<str:object_id>/output_audio",
        bots_api_views.OutputAudioView.as_view(),
        name="bot-output-audio",
    ),
    path(
        "bots/<str:object_id>/output_image",
        bots_api_views.OutputImageView.as_view(),
        name="bot-output-image",
    ),
    path(
        "bots/<str:object_id>/speech",
        bots_api_views.SpeechView.as_view(),
        name="bot-speech",
    ),
]

# catch any other paths and return a 404 json response - must be last
urlpatterns += [path("<path:any>", bots_api_views.NotFoundView.as_view())]
