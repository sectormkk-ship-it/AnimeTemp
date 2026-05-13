from datetime import timedelta

from django.utils import timezone

from .models import (
    Amistad,
    MensajePrivado,
    Notificacion,
)


def anime_nexus(request):

    if not request.user.is_authenticated:
        return {}

    # =====================================================
    # AMISTADES
    # =====================================================

    amistades = (
        Amistad.objects.filter(
            estado="aceptada",
            emisor=request.user,
        )
        |
        Amistad.objects.filter(
            estado="aceptada",
            receptor=request.user,
        )
    )

    amigos_nexus = []

    total_mensajes_no_leidos = 0

    for amistad in amistades:

        amigo = (
            amistad.receptor
            if amistad.emisor == request.user
            else amistad.emisor
        )

        # =================================================
        # ESTADO ONLINE
        # =================================================

        estado_online = "offline"

        perfil_amigo = getattr(amigo, "perfilusuario", None)

        if perfil_amigo and perfil_amigo.ultimo_online:

            diferencia = timezone.now() - perfil_amigo.ultimo_online

            if diferencia <= timedelta(minutes=2):
                estado_online = "online"

            elif diferencia <= timedelta(minutes=15):
                estado_online = "ausente"

        # =================================================
        # MENSAJES NO LEIDOS
        # =================================================

        no_leidos = MensajePrivado.objects.filter(
            remitente=amigo,
            destinatario=request.user,
            leido=False,
        ).count()

        total_mensajes_no_leidos += no_leidos

        # =================================================
        # LISTA AMIGOS NEXUS
        # =================================================

        amigos_nexus.append(
            {
                "usuario": amigo,
                "no_leidos": no_leidos,
                "estado_online": estado_online,
            }
        )

    # =====================================================
    # SOLICITUDES PENDIENTES
    # =====================================================

    solicitudes_pendientes_nexus = Amistad.objects.filter(
        receptor=request.user,
        estado="pendiente"
    ).order_by("-fecha")

    # =====================================================
    # NOTIFICACIONES
    # =====================================================

    notificaciones_nexus = Notificacion.objects.filter(
        usuario=request.user,
        leida=False
    ).order_by("-fecha")

    total_notificaciones_nexus = notificaciones_nexus.count()

    # =====================================================
    # RETURN
    # =====================================================

    return {
        "amigos_nexus": amigos_nexus,
        "total_mensajes_no_leidos": total_mensajes_no_leidos,
        "solicitudes_pendientes_nexus": solicitudes_pendientes_nexus,
        "notificaciones_nexus": notificaciones_nexus,
        "total_notificaciones_nexus": total_notificaciones_nexus,
    }