import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import User
from .models import MensajePrivado


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.usuario = self.scope["user"]
        self.usuario_id = self.scope["url_route"]["kwargs"]["usuario_id"]

        if self.usuario.is_anonymous:
            await self.close()
            return

        ids = sorted([int(self.usuario.id), int(self.usuario_id)])
        self.room_group_name = f"chat_{ids[0]}_{ids[1]}"

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code):
        if hasattr(self, "room_group_name"):
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )

    async def receive(self, text_data):
        data = json.loads(text_data)

        # Usuario escribiendo
        if data.get("typing"):
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "chat_typing",
                    "remitente": self.usuario.username,
                    "remitente_id": self.usuario.id,
                }
            )
            return

        mensaje_texto = data.get("mensaje", "").strip()

        if not mensaje_texto:
            return

        mensaje = await self.guardar_mensaje(mensaje_texto)
        foto = await self.obtener_foto(mensaje.remitente)

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "chat_message",
                "mensaje": mensaje.mensaje,
                "remitente": mensaje.remitente.username,
                "remitente_id": mensaje.remitente.id,
                "fecha": mensaje.fecha.strftime("%d/%m/%Y %H:%M"),
                "foto": foto,
            }
        )

    async def chat_message(self, event):
        await self.send(text_data=json.dumps({
            "mensaje": event["mensaje"],
            "remitente": event["remitente"],
            "remitente_id": event["remitente_id"],
            "fecha": event["fecha"],
            "foto": event.get("foto"),
            "es_mio": event["remitente_id"] == self.usuario.id,
        }))

    async def chat_typing(self, event):
        # No mostrar tu propio typing
        if event["remitente_id"] == self.usuario.id:
            return

        await self.send(text_data=json.dumps({
            "typing": True,
            "remitente": event["remitente"],
        }))

    @database_sync_to_async
    def guardar_mensaje(self, mensaje_texto):
        destinatario = User.objects.get(id=self.usuario_id)

        return MensajePrivado.objects.create(
            remitente=self.usuario,
            destinatario=destinatario,
            mensaje=mensaje_texto
        )

    @database_sync_to_async
    def obtener_foto(self, usuario):
        try:
            if usuario.perfilusuario.foto_perfil:
                return usuario.perfilusuario.foto_perfil.url
        except Exception:
            pass

        return "/static/img/default-profile.png"


class NotificacionesConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope["user"]

        if self.user.is_anonymous:
            await self.close()
            return

        self.group_name = f"notificaciones_{self.user.id}"

        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code):
        if hasattr(self, "group_name"):
            await self.channel_layer.group_discard(
                self.group_name,
                self.channel_name
            )

    async def enviar_notificacion(self, event):
        await self.send(text_data=json.dumps({
            "mensaje": event["mensaje"],
            "tipo": event["tipo"],
            "total": event["total"],
        }))
