from django.contrib import admin
from modeltranslation.admin import TranslationAdmin

from .models import StrikeUsuario
from .models import Anime, Favorito, Amistad, MensajePrivado
from .models import ReporteUsuario
from .models import Notificacion

@admin.register(ReporteUsuario)
class ReporteUsuarioAdmin(admin.ModelAdmin):
    list_display = (
        "reportante",
        "usuario_reportado",
        "motivo",
        "fecha",
        "revisado",
    )

    list_filter = (
        "motivo",
        "revisado",
        "fecha",
    )

    search_fields = (
        "reportante__username",
        "usuario_reportado__username",
        "descripcion",
    )


@admin.register(StrikeUsuario)
class StrikeUsuarioAdmin(admin.ModelAdmin):
    list_display = ("usuario", "admin", "motivo", "fecha")
    search_fields = ("usuario__username", "admin__username", "motivo")
    list_filter = ("fecha",)

@admin.register(Anime)
class AnimeAdmin(TranslationAdmin):
    pass


admin.site.register(Favorito)
admin.site.register(Amistad)
admin.site.register(MensajePrivado)

@admin.register(Notificacion)
class NotificacionAdmin(admin.ModelAdmin):
    list_display = ("usuario", "tipo", "mensaje", "leida", "fecha")
    list_filter = ("tipo", "leida", "fecha")
    search_fields = ("usuario__username", "mensaje")