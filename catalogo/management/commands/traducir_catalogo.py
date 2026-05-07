import time
from django.core.management.base import BaseCommand
from deep_translator import GoogleTranslator
from catalogo.models import Anime


class Command(BaseCommand):
    help = "Traduce automáticamente el catálogo de anime al español"

    def add_arguments(self, parser):
        parser.add_argument(
            "--desde",
            type=int,
            default=1
        )

        parser.add_argument(
            "--hasta",
            type=int,
            default=999999
        )

    def handle(self, *args, **options):

        desde = options["desde"]
        hasta = options["hasta"]

        traductor = GoogleTranslator(
            source="auto",
            target="es"
        )

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
                f"Iniciando traducción: {total} animes"
            )
        )

        for anime in animes:

            try:

                cambio = False

                # =========================
                # TITULO
                # =========================
                if anime.titulo and not anime.titulo_es:

                    anime.titulo_es = anime.titulo

                    cambio = True

                # =========================
                # DESCRIPCION
                # =========================
                if anime.descripcion:

                    descripcion_original = (
                        anime.descripcion.strip()
                    )

                    descripcion_traducida = (
                        anime.descripcion_es or ""
                    ).strip()

                    necesita_traduccion = (
                        not descripcion_traducida
                        or descripcion_traducida == descripcion_original
                    )

                    if necesita_traduccion:

                        texto = descripcion_original[:4500]

                        anime.descripcion_es = (
                            traductor.translate(texto)
                        )

                        cambio = True

                        time.sleep(0.4)

                # =========================
                # GENERO
                # =========================
                if anime.genero:

                    genero_actual = (
                        anime.genero_es or ""
                    ).strip()

                    if (
                        not genero_actual
                        or genero_actual == anime.genero.strip()
                    ):

                        anime.genero_es = traductor.translate(
                            anime.genero
                        )

                        cambio = True

                        time.sleep(0.2)

                # =========================
                # ESTADO
                # =========================
                if anime.estado:

                    traducciones_estado = {
                        "En emisión": "En emisión",
                        "Airing": "En emisión",
                        "Finished Airing": "Finalizado",
                        "Not yet aired": "Próximamente",
                        "Finalizado": "Finalizado",
                        "Próximamente": "Próximamente",
                    }

                    estado_actual = (
                        anime.estado_es or ""
                    ).strip()

                    necesita_estado = (
                        not estado_actual
                        or estado_actual == anime.estado.strip()
                    )

                    if necesita_estado:

                        anime.estado_es = (
                            traducciones_estado.get(
                                anime.estado,
                                traductor.translate(anime.estado)
                            )
                        )

                        cambio = True

                        time.sleep(0.2)

                # =========================
                # GUARDAR
                # =========================
                if cambio:

                    anime.save()

                    traducidos += 1

                    self.stdout.write(
                        self.style.SUCCESS(
                            f"Traducido: "
                            f"{anime.id} - {anime.titulo}"
                        )
                    )

                else:

                    omitidos += 1

                    self.stdout.write(
                        self.style.WARNING(
                            f"Omitido: "
                            f"{anime.id} - {anime.titulo}"
                        )
                    )

            except Exception as e:

                errores += 1

                self.stdout.write(
                    self.style.ERROR(
                        f"Error en "
                        f"{anime.id} - {anime.titulo}: {e}"
                    )
                )

                time.sleep(1)

        self.stdout.write(
            self.style.SUCCESS("Traducción terminada.")
        )

        self.stdout.write(
            self.style.SUCCESS(
                f"Traducidos: {traducidos}"
            )
        )

        self.stdout.write(
            self.style.WARNING(
                f"Omitidos: {omitidos}"
            )
        )

        self.stdout.write(
            self.style.ERROR(
                f"Errores: {errores}"
            )
        )