import json

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from .models import MensajeGlobalFeedback
from django.contrib.auth.models import User

from .models import MensajePrivado


def obtener_nivel_rol(rol):

    niveles = {
        "usuario": 0,
        "vip": 1,
        "helper": 2,
        "mod": 3,
        "admin": 4,
        "owner": 5,
    }

    return niveles.get(rol, 0)

# ============================================================
# CHAT PRIVADO EN TIEMPO REAL - NEXUS
# ============================================================

class ChatConsumer(AsyncWebsocketConsumer):

    async def connect(self):
        self.usuario = self.scope["user"]
        self.otro_usuario_id = self.scope["url_route"]["kwargs"]["usuario_id"]

        if self.usuario.is_anonymous:
            await self.close()
            return

        if not await self.usuario_existe(self.otro_usuario_id):
            await self.close()
            return

        ids = sorted([
            int(self.usuario.id),
            int(self.otro_usuario_id)
        ])

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
        try:
            data = json.loads(text_data)
        except json.JSONDecodeError:
            return

        # =========================
        # INDICADOR "ESCRIBIENDO..."
        # =========================
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

        # =========================
        # MENSAJE NORMAL
        # =========================
        mensaje_texto = data.get("mensaje", "")

        if not isinstance(mensaje_texto, str):
            return

        mensaje_texto = mensaje_texto.strip()

        if not mensaje_texto:
            return

        # Evita mensajes gigantes accidentales
        if len(mensaje_texto) > 1000:
            mensaje_texto = mensaje_texto[:1000]

        mensaje = await self.guardar_mensaje(mensaje_texto)
        foto = await self.obtener_foto_usuario(self.usuario.id)

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "chat_message",
                "mensaje": mensaje.mensaje,
                "remitente": self.usuario.username,
                "remitente_id": self.usuario.id,
                "fecha": mensaje.fecha.strftime("%d/%m/%Y %H:%M"),
                "foto": foto,
            }
        )

    async def chat_message(self, event):
        await self.send(text_data=json.dumps({
            "mensaje": event.get("mensaje", ""),
            "remitente": event.get("remitente", ""),
            "remitente_id": event.get("remitente_id"),
            "fecha": event.get("fecha", ""),
            "foto": event.get("foto", "/static/img/default-profile.png"),
            "es_mio": event.get("remitente_id") == self.usuario.id,
        }))

    async def chat_typing(self, event):
        if event.get("remitente_id") == self.usuario.id:
            return

        await self.send(text_data=json.dumps({
            "typing": True,
            "remitente": event.get("remitente", "Usuario"),
        }))

    # ========================================================
    # CONSULTAS A BASE DE DATOS
    # ========================================================

    @database_sync_to_async
    def usuario_existe(self, usuario_id):
        return User.objects.filter(id=usuario_id).exists()

    @database_sync_to_async
    def guardar_mensaje(self, mensaje_texto):
        destinatario = User.objects.get(id=self.otro_usuario_id)

        return MensajePrivado.objects.create(
            remitente=self.usuario,
            destinatario=destinatario,
            mensaje=mensaje_texto
        )

    @database_sync_to_async
    def obtener_foto_usuario(self, usuario_id):
        try:
            usuario = User.objects.select_related("perfilusuario").get(id=usuario_id)

            if usuario.perfilusuario.foto_perfil:
                return usuario.perfilusuario.foto_perfil.url

        except Exception:
            pass

        return "/static/img/default-profile.png"

# ========================================================
# FEDBACACK GLOBAL EN TIEMPO REAL - NEXUS
# ========================================================

class FeedbackGlobalConsumer(AsyncWebsocketConsumer):

    usuarios_online = {}

    async def connect(self):

        self.usuario = self.scope["user"]

        if self.usuario.is_anonymous:
            await self.close()
            return

        self.room_group_name = "feedback_global"

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        FeedbackGlobalConsumer.usuarios_online[self.channel_name] = await self.obtener_usuario_online(
            self.usuario
        )

        await self.accept()

        await self.enviar_lista_online()

    async def disconnect(self, close_code):

        if self.channel_name in FeedbackGlobalConsumer.usuarios_online:
            del FeedbackGlobalConsumer.usuarios_online[self.channel_name]

        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

        await self.enviar_lista_online()

    async def receive(self, text_data):

        try:
            data = json.loads(text_data)
        except json.JSONDecodeError:
            return

        mensaje = data.get("mensaje", "").strip()

        if not mensaje:
            return

        if len(mensaje) > 1000:
            mensaje = mensaje[:1000]

        mensaje_obj = await self.guardar_mensaje(
            self.usuario,
            mensaje
        )

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "feedback_message",
                "mensaje": mensaje_obj
            }
        )

    async def feedback_message(self, event):

        mensaje = event["mensaje"]

        mensaje["es_mio"] = mensaje.get("usuario_id") == self.usuario.id

        await self.send(text_data=json.dumps({
            "type": "feedback",
            "mensaje": mensaje
        }))

    async def feedback_online(self, event):

        await self.send(text_data=json.dumps({
            "type": "online",
            "total": event["total"],
            "usuarios": event["usuarios"]
        }))

    async def enviar_lista_online(self):

        usuarios_unicos = {}

        for usuario in FeedbackGlobalConsumer.usuarios_online.values():
            usuarios_unicos[usuario["id"]] = usuario

        usuarios = list(usuarios_unicos.values())

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "feedback_online",
                "total": len(usuarios),
                "usuarios": usuarios
            }
        )

    @database_sync_to_async
    def obtener_usuario_online(self, usuario):

        perfil = getattr(usuario, "perfilusuario", None)

        avatar = None

        if perfil and perfil.foto_perfil:
            avatar = perfil.foto_perfil.url

        return {
            "id": usuario.id,
            "username": usuario.username,
            "avatar": avatar,
            "es_creador": usuario.is_staff or usuario.is_superuser,
            "rol": getattr(perfil, "rol_nexus", "usuario") if perfil else "usuario",
            "banner": perfil.fondo_perfil.url if perfil and perfil.fondo_perfil else None,
        }

    @database_sync_to_async
    def guardar_mensaje(self, usuario, texto):

        mensaje = MensajeGlobalFeedback.objects.create(
            usuario=usuario,
            texto=texto
        )

        perfil = getattr(usuario, "perfilusuario", None)

        avatar = None

        if perfil and perfil.foto_perfil:
            avatar = perfil.foto_perfil.url

        rol = getattr(perfil, "rol_nexus", "usuario")

        return {
        "id": mensaje.id,
        "usuario_id": usuario.id,
        "username": usuario.username,
        "texto": mensaje.texto,
        "fecha": mensaje.fecha.strftime("%d/%m/%Y %H:%M"),
        "avatar": avatar,

        "rol": rol,
        "es_creador": rol == "owner" or usuario.is_superuser,
        "puede_borrar": obtener_nivel_rol(rol) >= 3 or usuario.is_staff or usuario.is_superuser,

        "es_mio": False
}
# ============================================================
# NOTIFICACIONES EN TIEMPO REAL - NEXUS
# ============================================================

class NotificacionesConsumer(AsyncWebsocketConsumer):

    async def connect(self):

        self.usuario = self.scope["user"]

        if self.usuario.is_anonymous:
            await self.close()
            return

        self.group_name = f"notificaciones_{self.usuario.id}"

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
            "mensaje": event.get("mensaje", ""),
            "tipo": event.get("tipo", "sistema"),
            "total": event.get("total", 0),
            "solicitud_id": event.get("solicitud_id"),
            "accion": event.get("accion"),

            "emisor_id": event.get("emisor_id"),
            "emisor_username": event.get("emisor_username"),
            "emisor_foto": event.get("emisor_foto"),

            "amigo_id": event.get("amigo_id"),
            "amigo_username": event.get("amigo_username"),
            "amigo_foto": event.get("amigo_foto"),
        }))
