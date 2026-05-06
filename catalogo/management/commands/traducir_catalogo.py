import time
from django.core.management.base import BaseCommand
from deep_translator import GoogleTranslator
from catalogo.models import Anime


class Command(BaseCommand):
    help = "Traduce automáticamente el catálogo de anime al español"

    def handle(self, *args, **kwargs):
        traductor = GoogleTranslator(source="auto", target="es")

        animes = Anime.objects.all().order_by("id")
        total = animes.count()
        traducidos = 0
        omitidos = 0
        errores = 0

        self.stdout.write(
            self.style.WARNING(f"Iniciando traducción del catálogo: {total} animes")
        )

        for anime in animes:
            try:
                cambio = False

                if anime.titulo and not getattr(anime, "titulo_es", None):
                    anime.titulo_es = anime.titulo
                    cambio = True

                if anime.descripcion and not getattr(anime, "descripcion_es", None):
                    texto = anime.descripcion[:4500]
                    anime.descripcion_es = traductor.translate(texto)
                    cambio = True
                    time.sleep(0.4)

                if anime.genero and not getattr(anime, "genero_es", None):
                    anime.genero_es = traductor.translate(anime.genero)
                    cambio = True
                    time.sleep(0.2)

                if anime.estado and not getattr(anime, "estado_es", None):
                    traducciones_estado = {
                        "En emisión": "En emisión",
                        "Airing": "En emisión",
                        "Finished Airing": "Finalizado",
                        "Not yet aired": "Próximamente",
                        "Finalizado": "Finalizado",
                        "Próximamente": "Próximamente",
                    }

                    anime.estado_es = traducciones_estado.get(
                        anime.estado,
                        traductor.translate(anime.estado)
                    )
                    cambio = True
                    time.sleep(0.2)

                if cambio:
                    anime.save()
                    traducidos += 1
                    self.stdout.write(
                        self.style.SUCCESS(f"Traducido: {anime.titulo}")
                    )
                else:
                    omitidos += 1

            except Exception as e:
                errores += 1
                self.stdout.write(
                    self.style.ERROR(f"Error traduciendo {anime.titulo}: {e}")
                )
                time.sleep(1)

        self.stdout.write(self.style.SUCCESS("Traducción terminada."))
        self.stdout.write(self.style.SUCCESS(f"Traducidos: {traducidos}"))
        self.stdout.write(self.style.WARNING(f"Omitidos: {omitidos}"))
        self.stdout.write(self.style.ERROR(f"Errores: {errores}"))