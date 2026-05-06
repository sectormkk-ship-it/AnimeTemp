import time
from django.core.management.base import BaseCommand
from deep_translator import GoogleTranslator

from catalogo.models import Anime


class Command(BaseCommand):
    help = "Traduce automáticamente el catálogo de anime al español, sobrescribiendo campos ES"

    def handle(self, *args, **kwargs):
        traductor = GoogleTranslator(source="auto", target="es")

        animes = Anime.objects.all()
        total = animes.count()
        traducidos = 0

        self.stdout.write(
            self.style.WARNING(
                f"Iniciando traducción forzada de {total} animes..."
            )
        )

        for anime in animes:
            try:
                if anime.titulo:
                    anime.titulo_es = anime.titulo

                if anime.descripcion:
                    anime.descripcion_es = traductor.translate(anime.descripcion[:4500])

                if anime.genero:
                    anime.genero_es = traductor.translate(anime.genero)

                if anime.estado:
                    anime.estado_es = traductor.translate(anime.estado)

                anime.save()
                traducidos += 1

                self.stdout.write(
                    self.style.SUCCESS(
                        f"Traducido: {anime.titulo}"
                    )
                )

                time.sleep(0.4)

            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(
                        f"Error traduciendo {anime.titulo}: {e}"
                    )
                )

        self.stdout.write(
            self.style.SUCCESS(
                f"Traducción terminada. Animes actualizados: {traducidos}"
            )
        )