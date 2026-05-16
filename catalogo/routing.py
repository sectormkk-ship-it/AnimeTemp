from django.urls import re_path

from .consumers import (
    ChatConsumer,
    NotificacionesConsumer,
    FeedbackGlobalConsumer,
)

websocket_urlpatterns = [

    # CHAT PRIVADO
    re_path(r"ws/chat/(?P<usuario_id>\d+)/$",ChatConsumer.as_asgi()),

    # FEEDBACK GLOBAL
    re_path(r"ws/feedback-global/$",FeedbackGlobalConsumer.as_asgi()),

    # NOTIFICACIONES
    re_path(r"ws/notificaciones/$",NotificacionesConsumer.as_asgi()),

]