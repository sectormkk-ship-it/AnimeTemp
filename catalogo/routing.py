from django.urls import re_path
from .consumers import ChatConsumer, NotificacionesConsumer

websocket_urlpatterns = [
    # CHAT (lo que ya tenías)
    re_path(r"ws/chat/(?P<usuario_id>\d+)/$", ChatConsumer.as_asgi()),

    # 🔔 NOTIFICACIONES NUEVAS
    re_path(r"ws/notificaciones/$", NotificacionesConsumer.as_asgi()),
]