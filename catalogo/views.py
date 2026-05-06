from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.core.management import call_command
from django.views.decorators.http import require_GET
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from .models import Notificacion

from .forms import PerfilUsuarioForm, ResenaForm
from .models import (Amistad,UsuarioSilenciado,Anime, Favorito,LikeResena,MensajePrivado,PerfilUsuario,Reporte,Resena,ReporteUsuario,StrikeUsuario,Notificacion,)
import os

# ============================================================
# CONFIGURACIÓN GENERAL DE IMÁGENES POR DEFECTO :D
# ============================================================

DEFAULT_PROFILE_IMAGE = "/static/img/default-profile.png"
DEFAULT_PROFILE_BANNER = "/static/img/default-banner.jpg"


def obtener_imagenes_perfil(usuario):
    """
    Devuelve la foto y el banner del perfil de un usuario.
    Si no tiene foto o banner personalizados, usa imágenes por defecto.
    """

    perfil_usuario, creado = PerfilUsuario.objects.get_or_create(usuario=usuario)

    foto_perfil = DEFAULT_PROFILE_IMAGE
    banner_perfil = DEFAULT_PROFILE_BANNER

    if perfil_usuario.foto_perfil:
        foto_perfil = perfil_usuario.foto_perfil.url

    if perfil_usuario.fondo_perfil:
        banner_perfil = perfil_usuario.fondo_perfil.url

    return foto_perfil, banner_perfil


# ============================================================
# INICIO / CATÁLOGO PRINCIPAL :D
# ============================================================

@require_GET
def actualizar_catalogo_render(request):
    token = request.GET.get("token")
    token_seguro = os.environ.get("UPDATE_CATALOG_TOKEN")

    if not token_seguro or token != token_seguro:
        return JsonResponse({
            "ok": False,
            "error": "No autorizado"
        }, status=403)

    try:
        call_command("actualizar_animes_emision")

        return JsonResponse({
            "ok": True,
            "mensaje": "Catálogo actualizado correctamente"
        })

    except Exception as e:
        return JsonResponse({
            "ok": False,
            "error": str(e)
        }, status=500)

def inicio(request):
    busqueda = request.GET.get("buscar")
    temporada = request.GET.get("temporada")
    genero = request.GET.get("genero")
    estado = request.GET.get("estado")

    animes = Anime.objects.all().order_by("-creado_en")

    if busqueda:
        animes = animes.filter(titulo__icontains=busqueda)

    if temporada:
        animes = animes.filter(temporada__iexact=temporada)

    if genero:
        animes = animes.filter(genero__icontains=genero)

    if estado:
        animes = animes.filter(estado__iexact=estado)

    return render(
        request,
        "catalogo/inicio.html",
        {
            "animes": animes,
            "busqueda": busqueda,
            "temporada_actual": temporada,
            "genero_actual": genero,
            "estado_actual": estado,
        },
    )


# ============================================================
# REGISTRO DE USUARIOS :D
# ============================================================

def registro(request):
    if request.method == "POST":
        form = UserCreationForm(request.POST)

        if form.is_valid():
            form.save()
            return redirect("login")
    else:
        form = UserCreationForm()

    return render(request, "catalogo/registro.html", {"form": form})


# ============================================================
# EMOJIS PERSONALIZADOS EN RESEÑAS :D
# ============================================================

def convertir_emojis(texto):
    emojis = {
        ":naruto:": '<img src="/static/emojis/naruto.png" class="emoji-anime">',
        ":luffy:": '<img src="/static/emojis/luffy.png" class="emoji-anime">',
        ":gojo:": '<img src="/static/emojis/gojo.png" class="emoji-anime">',
        ":nezuko:": '<img src="/static/emojis/nezuko.png" class="emoji-anime">',
    }

    for codigo, imagen in emojis.items():
        texto = texto.replace(codigo, imagen)

    return texto


# ============================================================
# DETALLE DE ANIME / RESEÑAS:D
# ============================================================

def detalle_anime(request, anime_id):
    anime = get_object_or_404(Anime, id=anime_id)
    resenas = anime.resenas.all().order_by("-fecha")

    for resena in resenas:
        resena.texto = convertir_emojis(resena.texto)

    if request.method == "POST" and request.user.is_authenticated:
        form = ResenaForm(request.POST)

        if form.is_valid():
            Resena.objects.update_or_create(
                usuario=request.user,
                anime=anime,
                defaults={
                    "texto": convertir_emojis(form.cleaned_data["texto"]),
                },
            )

            return redirect("detalle_anime", anime_id=anime.id)
    else:
        form = ResenaForm()

    es_favorito = False

    if request.user.is_authenticated:
        es_favorito = Favorito.objects.filter(
            usuario=request.user,
            anime=anime,
        ).exists()

    return render(
        request,
        "catalogo/detalle.html",
        {
            "anime": anime,
            "resenas": resenas,
            "resena_form": form,
            "es_favorito": es_favorito,
        },
    )


@login_required
@require_POST
def like_resena(request, resena_id):
    resena = get_object_or_404(Resena, id=resena_id)

    like, created = LikeResena.objects.get_or_create(
        usuario=request.user,
        resena=resena,
    )

    if created:
        liked = True
    else:
        like.delete()
        liked = False

    return JsonResponse(
        {
            "ok": True,
            "liked": liked,
            "total_likes": resena.likes.count(),
        }
    )


# ============================================================
# RESEÑAS DEL USUARIO - AJAX PARA MENÚ NEXUS :D
# ============================================================
# Esta vista responde al fetch:
# /usuario/<usuario_id>/resenas/
#
# Devuelve:
# - nombre del usuario
# - foto de perfil real o default
# - banner real o default
# - lista de reseñas del usuario
# ============================================================

@login_required
def usuario_resenas_ajax(request, usuario_id):
    usuario = get_object_or_404(User, id=usuario_id)

    # Foto de perfil y banner del usuario
    foto_perfil, banner_perfil = obtener_imagenes_perfil(usuario)

    # Reseñas del usuario
    resenas = Resena.objects.filter(
        usuario=usuario
    ).select_related("anime").order_by("-fecha")

    # Datos que se envían al JavaScript
    resenas_data = []

    for resena in resenas:
        resenas_data.append({
            "anime": resena.anime.titulo,
            "imagen": resena.anime.imagen,
            "texto": resena.texto,
            "puntuacion": resena.puntuacion,
            "fecha": resena.fecha.strftime("%d/%m/%Y"),
        })

    return JsonResponse({
        "ok": True,
        "usuario_nombre": usuario.username,
        "usuario_foto": foto_perfil,
        "usuario_banner": banner_perfil,
        "total": resenas.count(),
        "resenas": resenas_data,
    })


# ============================================================
# FAVORITOS :D
# ============================================================

@login_required
def agregar_favorito(request, anime_id):
    anime = get_object_or_404(Anime, id=anime_id)

    Favorito.objects.get_or_create(
        usuario=request.user,
        anime=anime,
    )

    return redirect("perfil")


@login_required
def agregar_favorito_ajax(request, anime_id):
    anime = get_object_or_404(Anime, id=anime_id)

    Favorito.objects.get_or_create(
        usuario=request.user,
        anime=anime,
    )

    return JsonResponse(
        {
            "ok": True,
            "mensaje": "Anime agregado a favoritos",
            "anime_id": anime.id,
            "titulo": anime.titulo,
            "imagen": anime.imagen,
        }
    )


@login_required
def quitar_favorito(request, anime_id):
    anime = get_object_or_404(Anime, id=anime_id)

    Favorito.objects.filter(
        usuario=request.user,
        anime=anime,
    ).delete()

    return redirect("favoritos")


@login_required
def quitar_favorito_ajax(request, anime_id):
    anime = get_object_or_404(Anime, id=anime_id)

    Favorito.objects.filter(
        usuario=request.user,
        anime=anime,
    ).delete()

    return JsonResponse(
        {
            "ok": True,
            "anime_id": anime.id,
            "titulo": anime.titulo,
            "imagen": anime.imagen,
        }
    )


@login_required
def ver_favoritos(request):
    favoritos = Favorito.objects.filter(usuario=request.user)

    return render(
        request,
        "catalogo/favoritos.html",
        {"favoritos": favoritos},
    )


# ============================================================
# PERFIL PRIVADO / EDITAR PERFIL :D
# ============================================================

@login_required
def perfil(request):
    favoritos = Favorito.objects.filter(usuario=request.user)
    favoritos_count = favoritos.count()

    perfil_usuario, creado = PerfilUsuario.objects.get_or_create(usuario=request.user)

    busqueda = request.GET.get("buscar", "")

    animes_disponibles = Anime.objects.exclude(favorito__usuario=request.user)

    if busqueda:
        animes_disponibles = animes_disponibles.filter(titulo__icontains=busqueda)

    animes_disponibles = animes_disponibles[:8]

    return render(
        request,
        "catalogo/perfil.html",
        {
            "favoritos_count": favoritos_count,
            "perfil_usuario": perfil_usuario,
            "favoritos": favoritos,
            "animes_disponibles": animes_disponibles,
            "busqueda": busqueda,
        },
    )


@login_required
def editar_perfil(request):
    perfil_usuario, creado = PerfilUsuario.objects.get_or_create(usuario=request.user)

    if request.method == "POST":
        form = PerfilUsuarioForm(
            request.POST,
            request.FILES,
            instance=perfil_usuario,
        )

        if form.is_valid():
            perfil_usuario = form.save(commit=False)

            if form.cleaned_data.get("borrar_foto"):
                if perfil_usuario.foto_perfil:
                    perfil_usuario.foto_perfil.delete(save=False)
                perfil_usuario.foto_perfil = None

            if form.cleaned_data.get("borrar_fondo"):
                if perfil_usuario.fondo_perfil:
                    perfil_usuario.fondo_perfil.delete(save=False)
                perfil_usuario.fondo_perfil = None

            perfil_usuario.save()

            return redirect("perfil")
    else:
        form = PerfilUsuarioForm(instance=perfil_usuario)

    return render(
        request,
        "catalogo/editar_perfil.html",
        {"form": form},
    )


@login_required
def perfil_publico(request, usuario_id):
    usuario_perfil = get_object_or_404(User, id=usuario_id)

    perfil_usuario, creado = PerfilUsuario.objects.get_or_create(
        usuario=usuario_perfil
    )

    favoritos = Favorito.objects.filter(usuario=usuario_perfil)
    favoritos_count = favoritos.count()

    return render(
        request,
        "catalogo/perfil_publico.html",
        {
            "usuario_perfil": usuario_perfil,
            "perfil_usuario": perfil_usuario,
            "favoritos": favoritos,
            "favoritos_count": favoritos_count,
        },
    )


# ============================================================
# BÚSQUEDAS AJAX :D
# ============================================================

@login_required
def buscar_animes_ajax(request):
    busqueda = request.GET.get("buscar", "")

    animes = Anime.objects.filter(titulo__icontains=busqueda).exclude(
        favorito__usuario=request.user
    )[:8]

    resultados = []

    for anime in animes:
        resultados.append(
            {
                "id": anime.id,
                "titulo": anime.titulo,
                "imagen": anime.imagen,
            }
        )

    return JsonResponse({"resultados": resultados})


@login_required
def buscar_usuarios(request):
    busqueda = request.GET.get("buscar", "")

    usuarios = User.objects.exclude(id=request.user.id)

    if busqueda:
        usuarios = usuarios.filter(username__icontains=busqueda)

    return render(
        request,
        "catalogo/buscar_usuarios.html",
        {
            "usuarios": usuarios,
            "busqueda": busqueda,
        },
    )


# ============================================================
# ANIMES EN EMISIÓN :D
# ============================================================

def emision(request):
    dia = request.GET.get("dia")

    animes = Anime.objects.filter(
        estado__iexact="En emisión"
    ).order_by("-creado_en")

    dias_map = {
        "monday": 0,
        "tuesday": 1,
        "wednesday": 2,
        "thursday": 3,
        "friday": 4,
        "saturday": 5,
        "sunday": 6,
    }

    if dia in dias_map:
        animes = [
            anime for anime in animes
            if anime.fecha_emision and anime.fecha_emision.weekday() == dias_map[dia]
        ]

    return render(
        request,
        "catalogo/emision.html",
        {
            "animes": animes,
            "dia_actual": dia,
        },
    )


# ============================================================
# SISTEMA SOCIAL / AMISTADES :D
# ============================================================

@login_required
def enviar_solicitud_amistad(request, usuario_id):
    receptor = get_object_or_404(User, id=usuario_id)

    if request.user == receptor:
        return redirect("buscar_usuarios")

    solicitud_existente = Amistad.objects.filter(
        emisor=request.user,
        receptor=receptor,
        estado="pendiente"
    ).first()

    if solicitud_existente:
        return redirect("buscar_usuarios")

    amistad_existente = Amistad.objects.filter(
        emisor=request.user,
        receptor=receptor,
        estado="aceptada"
    ).exists() or Amistad.objects.filter(
        emisor=receptor,
        receptor=request.user,
        estado="aceptada"
    ).exists()

    if amistad_existente:
        return redirect("buscar_usuarios")

    solicitud = Amistad.objects.create(
        emisor=request.user,
        receptor=receptor,
        estado="pendiente"
    )

    Notificacion.objects.create(
        usuario=receptor,
        tipo="amistad",
        mensaje=f"👥 {request.user.username} quiere agregarte como amigo.",
        solicitud=solicitud,
    )

    enviar_notificacion_nexus(
        receptor,
        f"👥 {request.user.username} quiere agregarte como amigo.",
        "amistad",
        solicitud.id  # 🔥 ESTA LINEA
    )

    return redirect("buscar_usuarios")


@login_required
def solicitudes_amistad(request):
    solicitudes = Amistad.objects.filter(receptor=request.user, estado="pendiente")

    amigos = Amistad.objects.filter(
        estado="aceptada", emisor=request.user
    ) | Amistad.objects.filter(estado="aceptada", receptor=request.user)

    return render(
        request,
        "catalogo/solicitudes.html",
        {
            "solicitudes": solicitudes,
            "amigos": amigos,
        },
    )


@login_required
def aceptar_solicitud(request, solicitud_id):
    solicitud = get_object_or_404(
        Amistad, id=solicitud_id, receptor=request.user, estado="pendiente"
    )

    solicitud.estado = "aceptada"
    solicitud.save()
    Notificacion.objects.filter(solicitud=solicitud).update(leida=True)

    return redirect("solicitudes_amistad")


@login_required
def rechazar_solicitud(request, solicitud_id):
    solicitud = get_object_or_404(
        Amistad, id=solicitud_id, receptor=request.user, estado="pendiente"
    )

    solicitud.delete()
    Notificacion.objects.filter(solicitud=solicitud).delete()

    return redirect("solicitudes_amistad")


@login_required
def centro_social(request):
    solicitudes = Amistad.objects.filter(receptor=request.user, estado="pendiente")

    amigos = Amistad.objects.filter(
        estado="aceptada", emisor=request.user
    ) | Amistad.objects.filter(estado="aceptada", receptor=request.user)

    return render(
        request,
        "catalogo/social.html",
        {
            "solicitudes": solicitudes,
            "amigos": amigos,
        },
    )


@login_required
def eliminar_amigo(request, usuario_id):
    amigo = get_object_or_404(User, id=usuario_id)

    Amistad.objects.filter(
        emisor=request.user,
        receptor=amigo,
        estado="aceptada",
    ).delete()

    Amistad.objects.filter(
        emisor=amigo,
        receptor=request.user,
        estado="aceptada",
    ).delete()

    return JsonResponse({"ok": True})


@login_required
def bloquear_usuario(request, usuario_id):
    # Por ahora solo elimina la amistad.
    # Después podés crear un modelo BloqueoUsuario real.
    amigo = get_object_or_404(User, id=usuario_id)

    Amistad.objects.filter(emisor=request.user, receptor=amigo).delete()
    Amistad.objects.filter(emisor=amigo, receptor=request.user).delete()

    return JsonResponse({"ok": True})


@login_required
def silenciar_usuario(request, usuario_id):
    usuario_obj = get_object_or_404(User, id=usuario_id)

    silenciado, creado = UsuarioSilenciado.objects.get_or_create(
        usuario=request.user,
        usuario_silenciado=usuario_obj
    )

    if not creado:
        silenciado.delete()
        return JsonResponse({
            "ok": True,
            "silenciado": False,
            "mensaje": f"{usuario_obj.username} ya no está silenciado."
        })

    return JsonResponse({
        "ok": True,
        "silenciado": True,
        "mensaje": f"{usuario_obj.username} fue silenciado."
    })


# ============================================================
# REPORTES :D y staff
# ============================================================

@staff_member_required
def dar_strike_usuario(request, usuario_id):
    usuario = get_object_or_404(User, id=usuario_id)

    # Crear strike
    StrikeUsuario.objects.create(
        usuario=usuario,
        admin=request.user,
        motivo="Reporte confirmado",
        descripcion="Aplicado desde panel de reportes"
    )

    # Notificación de strike
    Notificacion.objects.create(
        usuario=usuario,
        tipo="strike",
        mensaje="⚠ Recibiste un strike por comportamiento indebido."
    )
    enviar_notificacion_nexus(
    usuario,
    "⚠ Recibiste un strike por comportamiento indebido.",
    "strike"
    )
    total_strikes = StrikeUsuario.objects.filter(usuario=usuario).count()

    # Auto suspensión
    if total_strikes >= 3 and not usuario.is_staff:
        usuario.is_active = False
        usuario.save()

        # Notificación de suspensión
        Notificacion.objects.create(
            usuario=usuario,
            tipo="sistema",
            mensaje="🚫 Tu cuenta fue suspendida por acumulación de strikes."
        )
        enviar_notificacion_nexus(
        usuario,
        "🚫 Tu cuenta fue suspendida por acumulación de strikes.",
        "sistema"
        )
    return redirect("panel_reportes")

@staff_member_required
def marcar_reporte_usuario_revisado(request, reporte_id):
    reporte = get_object_or_404(ReporteUsuario, id=reporte_id)
    reporte.revisado = True
    reporte.save()

    return redirect("panel_reportes")


@staff_member_required
def suspender_usuario_reportado(request, usuario_id):
    usuario = get_object_or_404(User, id=usuario_id)

    if not usuario.is_staff:
        usuario.is_active = False
        usuario.save()

    return redirect("panel_reportes")


@staff_member_required
def eliminar_reporte_usuario(request, reporte_id):
    reporte = get_object_or_404(ReporteUsuario, id=reporte_id)
    reporte.delete()

    return redirect("panel_reportes")

@login_required
def reportar_usuario(request, usuario_id):
    usuario_reportado = get_object_or_404(User, id=usuario_id)

    if request.user != usuario_reportado:
        Reporte.objects.create(
            reportante=request.user,
            usuario_reportado=usuario_reportado,
            tipo="usuario",
            motivo="Reporte enviado desde el menú Nexus.",
        )

    return JsonResponse({"ok": True})


@login_required
def reportar_bug(request):
    motivo = request.POST.get("motivo", "").strip()

    if motivo:
        Reporte.objects.create(
            reportante=request.user,
            tipo="bug",
            motivo=motivo,
        )

    return JsonResponse({"ok": True})


@staff_member_required
def panel_reportes(request):
    reportes_sistema = Reporte.objects.all().order_by("-fecha")
    reportes_usuarios = ReporteUsuario.objects.all().order_by("-fecha")

    for reporte in reportes_usuarios:
        reporte.total_strikes = StrikeUsuario.objects.filter(
            usuario=reporte.usuario_reportado
        ).count()

    return render(request, "catalogo/panel_reportes.html", {
        "reportes_sistema": reportes_sistema,
        "reportes_usuarios": reportes_usuarios,
    })

@staff_member_required
def quitar_strike_usuario(request, usuario_id):
    usuario = get_object_or_404(User, id=usuario_id)

    ultimo_strike = StrikeUsuario.objects.filter(
        usuario=usuario
    ).order_by("-fecha").first()

    if ultimo_strike:
        ultimo_strike.delete()

    total_strikes = StrikeUsuario.objects.filter(usuario=usuario).count()

    if total_strikes < 3 and not usuario.is_active:
        usuario.is_active = True
        usuario.save()

    return redirect("panel_reportes")
# ============================================================
# CHAT PRIVADO / MENSAJES :D
# ============================================================

@login_required
def chat_privado(request, usuario_id):
    amigo = get_object_or_404(User, id=usuario_id)

    mensajes = MensajePrivado.objects.filter(
        remitente__in=[request.user, amigo],
        destinatario__in=[request.user, amigo],
    ).order_by("fecha")

    MensajePrivado.objects.filter(
        remitente=amigo,
        destinatario=request.user,
        leido=False,
    ).update(leido=True)

    return render(
        request,
        "catalogo/chat_privado.html",
        {
            "amigo": amigo,
            "mensajes": mensajes,
        },
    )


@login_required
def obtener_mensajes(request, usuario_id):
    amigo = get_object_or_404(User, id=usuario_id)

    MensajePrivado.objects.filter(
        remitente=amigo,
        destinatario=request.user,
        leido=False,
    ).update(leido=True)

    mensajes = MensajePrivado.objects.filter(
        remitente__in=[request.user, amigo],
        destinatario__in=[request.user, amigo],
    ).order_by("fecha")

    data = []

    for mensaje in mensajes:
        foto, banner = obtener_imagenes_perfil(mensaje.remitente)

        data.append(
            {
                "remitente": mensaje.remitente.username,
                "mensaje": mensaje.mensaje,
                "fecha": mensaje.fecha.strftime("%d/%m/%Y %H:%M"),
                "es_mio": mensaje.remitente == request.user,
                "foto": foto,
            }
        )

    total_no_leidos = MensajePrivado.objects.filter(
        destinatario=request.user,
        leido=False,
    ).count()

    return JsonResponse(
        {
            "amigo": amigo.username,
            "mensajes": data,
            "total_no_leidos": total_no_leidos,
        }
    )


@login_required
@require_POST
def enviar_mensaje_ajax(request, usuario_id):
    destinatario = get_object_or_404(User, id=usuario_id)
    texto = request.POST.get("mensaje", "").strip()

    if not texto:
        return JsonResponse({"ok": False, "error": "El mensaje está vacío."})

    mensaje = MensajePrivado.objects.create(
        remitente=request.user,
        destinatario=destinatario,
        mensaje=texto,
    )

    return JsonResponse(
        {
            "ok": True,
            "mensaje": {
                "remitente": mensaje.remitente.username,
                "mensaje": mensaje.mensaje,
                "fecha": mensaje.fecha.strftime("%d/%m/%Y %H:%M"),
                "es_mio": True,
            },
        }
    )


@login_required
def bandeja_mensajes(request):
    amistades = Amistad.objects.filter(
        estado="aceptada", emisor=request.user
    ) | Amistad.objects.filter(estado="aceptada", receptor=request.user)

    amigos_ids = set()

    for amistad in amistades:
        if amistad.emisor == request.user:
            amigos_ids.add(amistad.receptor.id)
        else:
            amigos_ids.add(amistad.emisor.id)

    conversaciones = []

    for amigo_id in amigos_ids:
        amigo = User.objects.get(id=amigo_id)

        ultimo_mensaje = (
            MensajePrivado.objects.filter(
                remitente__in=[request.user, amigo],
                destinatario__in=[request.user, amigo],
            )
            .order_by("-fecha")
            .first()
        )

        no_leidos = MensajePrivado.objects.filter(
            remitente=amigo,
            destinatario=request.user,
            leido=False,
        ).count()

        silenciado = UsuarioSilenciado.objects.filter(
           usuario=request.user,
           usuario_silenciado=amigo
           ).exists()

        conversaciones.append(
            {
                "amigo": amigo,
                "ultimo_mensaje": ultimo_mensaje,
                "no_leidos": no_leidos,
            }
        )

    conversaciones.sort(
        key=lambda c: (
            c["ultimo_mensaje"].fecha if c["ultimo_mensaje"] else timezone.now()
        ),
        reverse=True,
    )

    return render(
        request,
        "catalogo/bandeja_mensajes.html",
        {
            "conversaciones": conversaciones,
        },
    )
    
    
@login_required
@require_POST
def reportar_usuario(request, usuario_id):
    usuario_reportado = get_object_or_404(User, id=usuario_id)

    motivo = request.POST.get("motivo")
    descripcion = request.POST.get("descripcion", "").strip()

    if not motivo:
        return JsonResponse({
            "ok": False,
            "mensaje": "Debes seleccionar un motivo."
        })

    ReporteUsuario.objects.create(
        reportante=request.user,
        usuario_reportado=usuario_reportado,
        motivo=motivo,
        descripcion=descripcion,
    )

    return JsonResponse({
        "ok": True,
        "mensaje": f"Reporte enviado contra {usuario_reportado.username}."
    })    
    
    
@login_required
def marcar_notificaciones_leidas(request):
    Notificacion.objects.filter(
        usuario=request.user,
        leida=False
    ).exclude(
        tipo="amistad",
        solicitud__estado="pendiente"
    ).update(leida=True)

    return JsonResponse({"ok": True})

def enviar_notificacion_nexus(usuario, mensaje, tipo="sistema", solicitud_id=None):
    total = Notificacion.objects.filter(
        usuario=usuario,
        leida=False
    ).count()

    channel_layer = get_channel_layer()

    async_to_sync(channel_layer.group_send)(
        f"notificaciones_{usuario.id}",
        {
            "type": "enviar_notificacion",
            "mensaje": mensaje,
            "tipo": tipo,
            "total": total,
            "solicitud_id": solicitud_id,
        }
    )
    
    
@require_GET
def traducir_catalogo_render(request):
    token = request.GET.get("token")
    token_seguro = os.environ.get("UPDATE_CATALOG_TOKEN")

    if not token_seguro or token != token_seguro:
        return JsonResponse({"ok": False, "error": "No autorizado"}, status=403)

    try:
        call_command("traducir_catalogo")
        return JsonResponse({"ok": True, "mensaje": "Catálogo traducido correctamente"})
    except Exception as e:
        return JsonResponse({"ok": False, "error": str(e)}, status=500)    
    
    
@require_GET
def importar_catalogo_render(request):
    import os
    from django.core.management import call_command

    token = request.GET.get("token")
    token_seguro = os.environ.get("UPDATE_CATALOG_TOKEN")

    if not token_seguro or token != token_seguro:
        return JsonResponse({"ok": False, "error": "No autorizado"}, status=403)

    try:
        call_command("importar_animes", paginas=5)

        return JsonResponse({
            "ok": True,
            "mensaje": "Catálogo importado correctamente"
        })

    except Exception as e:
        return JsonResponse({
            "ok": False,
            "error": str(e)
        }, status=500)    