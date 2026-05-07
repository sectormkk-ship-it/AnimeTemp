import time
from django.core.management.base import BaseCommand
from deep_translator import GoogleTranslator
from catalogo.models import Anime


class Command(BaseCommand):
    help = "Traduce automáticamente el catálogo de anime al español"

    def add_arguments(self, parser):
        parser.add_argument("--desde", type=int, default=1)
        parser.add_argument("--hasta", type=int, default=999999)

    def handle(self, *args, **options):
        desde = options["desde"]
        hasta = options["hasta"]

        traductor = GoogleTranslator(source="auto", target="es")

        animes = Anime.objects.filter(
            id__gte=desde,
            id__lte=hasta
        ).order_by("id")

        total = animes.count()
        traducidos = 0
        omitidos = 0
        errores = 0

        self.stdout.write(
            self.style.WARNING(
                f"Iniciando traducción del catálogo: {total} animes"
            )
        )

        for anime in animes:
            try:
                cambio = False

                if anime.titulo and not anime.titulo_es:
                    anime.titulo_es = anime.titulo
                    cambio = True

                if anime.descripcion:
                    necesita_traduccion = (
                        not anime.descripcion_es
                        or anime.descripcion_es.strip() == anime.descripcion.strip()
                    )

                    if necesita_traduccion:
                        texto = anime.descripcion[:4500]
                        anime.descripcion_es = traductor.translate(texto)
                        cambio = True
                        time.sleep(0.4)

                if anime.genero:
                    necesita_genero = (
                        not anime.genero_es
                        or anime.genero_es.strip() == anime.genero.strip()
                    )

                    if necesita_genero:
                        anime.genero_es = traductor.translate(anime.genero)
                        cambio = True
                        time.sleep(0.2)

                if anime.estado:
                    traducciones_estado = {
                        "En emisión": "En emisión",
                        "Airing": "En emisión",
                        "Finished Airing": "Finalizado",
                        "Not yet aired": "Próximamente",
                        "Finalizado": "Finalizado",
                        "Próximamente": "Próximamente",
                    }

                    estado_traducido = traducciones_estado.get(anime.estado)

                    necesita_estado = (
                        not anime.estado_es
                        or anime.estado_es.strip() == anime.estado.strip()
                        or anime.estado_es in ["Airing", "Finished Airing", "Not yet aired"]
                    )

                    if necesita_estado:
                        if estado_traducido:
                            anime.estado_es = estado_traducido
                        else:
                            anime.estado_es = traductor.translate(anime.estado)

                        cambio = True
                        time.sleep(0.2)

                if cambio:
                    anime.save()
                    traducidos += 1

                    self.stdout.write(
                        self.style.SUCCESS(
                            f"Traducido/corregido: {anime.id} - {anime.titulo}"
                        )
                    )
                else:
                    omitidos += 1

                    self.stdout.write(
                        self.style.WARNING(
                            f"Omitido: {anime.id} - {anime.titulo}"
                        )
                    )

            except Exception as e:
                errores += 1

                self.stdout.write(
                    self.style.ERROR(
                        f"Error traduciendo {anime.id} - {anime.titulo}: {e}"
                    )
                )

                time.sleep(1)

        self.stdout.write(self.style.SUCCESS("Traducción terminada."))
        self.stdout.write(self.style.SUCCESS(f"Traducidos/corregidos: {traducidos}"))
        self.stdout.write(self.style.WARNING(f"Omitidos: {omitidos}"))
        self.stdout.write(self.style.ERROR(f"Errores: {errores}"))