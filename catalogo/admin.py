from django.contrib import admin
from modeltranslation.admin import TranslationAdmin

from .models import SeguimientoAnime
from .models import StrikeUsuario
from .models import MensajeGlobalFeedback
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
    
@admin.register(SeguimientoAnime)
class SeguimientoAnimeAdmin(admin.ModelAdmin):
    list_display = ("usuario", "anime", "estado", "capitulos_vistos", "actualizado_en")
    list_filter = ("estado", "actualizado_en")
    search_fields = ("usuario__username", "anime__titulo")    
    
@admin.register(MensajeGlobalFeedback)
class MensajeGlobalFeedbackAdmin(admin.ModelAdmin):
    list_display = ("usuario", "texto_corto", "fecha")
    search_fields = ("usuario__username", "texto")
    list_filter = ("fecha",)
    ordering = ("-fecha",)

    def texto_corto(self, obj):
        return obj.texto[:80]    