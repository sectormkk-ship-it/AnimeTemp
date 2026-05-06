from .models import Amistad, MensajePrivado, Notificacion
from django.db.models import Q

def anime_nexus(request):
    if not request.user.is_authenticated:
        return {}

    # =========================
    # AMIGOS
    # =========================
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

        no_leidos = MensajePrivado.objects.filter(
            remitente=amigo,
            destinatario=request.user,
            leido=False,
        ).count()

        total_mensajes_no_leidos += no_leidos

        amigos_nexus.append(
            {
                "usuario": amigo,
                "no_leidos": no_leidos,
            }
        )

    # =========================
    # NOTIFICACIONES NUEVAS
    # =========================
    notificaciones_nexus = Notificacion.objects.filter(
    Q(usuario=request.user, leida=False) |
    Q(usuario=request.user, tipo="amistad", solicitud__estado="pendiente")
    ).distinct().order_by("-fecha")
    
    total_notificaciones_nexus = Notificacion.objects.filter(
        usuario=request.user,
        leida=False
    ).count()

    # =========================
    # RETURN FINAL
    # =========================
    return {
        "amigos_nexus": amigos_nexus,
        "total_mensajes_no_leidos": total_mensajes_no_leidos,
        "notificaciones_nexus": notificaciones_nexus,
        "total_notificaciones_nexus": total_notificaciones_nexus,
    }