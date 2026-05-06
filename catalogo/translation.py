from modeltranslation.translator import register, TranslationOptions
from .models import Anime


@register(Anime)
class AnimeTranslationOptions(TranslationOptions):
    fields = (
        'titulo',
        'descripcion',
        'genero',
        'estado',
    )