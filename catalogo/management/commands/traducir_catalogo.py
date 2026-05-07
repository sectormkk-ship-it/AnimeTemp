import time
from django.core.management.base import BaseCommand
from django.db.models import Q, F
from deep_translator import GoogleTranslator
from catalogo.models import Anime


class Command(BaseCommand):
    help = "Traduce solo animes pendientes sin cargar los ya traducidos"

    def add_arguments(self, parser):
        parser.add_argument("--desde", type=int, default=1)
        parser.add_argument("--hasta", type=int, default=999999)
        parser.add_argument("--limite", type=int, default=30)

    def handle(self, *args, **options):
        desde = options["desde"]
        hasta = options["hasta"]
        limite = options["limite"]

        traductor = GoogleTranslator(source="auto", target="es")

        pendientes = Anime.objects.filter(
            id__gte=desde,
            id__lte=hasta
        ).filter(
            Q(descripcion_es__isnull=True) |
            Q(descripcion_es="") |
            Q(descripcion_es=F("descripcion")) |
            Q(genero_es__isnull=True) |
            Q(genero_es="") |
            Q(genero_es=F("genero")) |
            Q(estado_es__isnull=True) |
            Q(estado_es="") |
            Q(estado_es=F("estado")) |
            Q(titulo_es__isnull=True) |
            Q(titulo_es="")
        ).order_by("id")[:limite]

        total_pendientes = pendientes.count()

        traducidos = 0
        errores = 0

        self.stdout.write(
            self.style.WARNING(
                f"Pendientes cargados para esta ejecución: {total_pendientes}"
            )
        )

        if total_pendientes == 0:
            self.stdout.write(
                self.style.SUCCESS("No hay animes pendientes para traducir.")
            )
            return

        for anime in pendientes:
            try:
                cambio = False

                if anime.titulo and not anime.titulo_es:
                    anime.titulo_es = anime.titulo
                    cambio = True

                if anime.descripcion:
                    original = anime.descripcion.strip()
                    actual = (anime.descripcion_es or "").strip()

                    if not actual or actual == original:
                        anime.descripcion_es = traductor.translate(original[:4500])
                        cambio = True
                        time.sleep(0.4)

                if anime.genero:
                    genero_original = anime.genero.strip()
                    genero_actual = (anime.genero_es or "").strip()

                    if not genero_actual or genero_actual == genero_original:
                        anime.genero_es = traductor.translate(genero_original)
                        cambio = True
                        time.sleep(0.2)

                if anime.estado:
                    traducciones_estado = {
                        "Airing": "En emisión",
                        "Finished Airing": "Finalizado",
                        "Not yet aired": "Próximamente",
                        "En emisión": "En emisión",
                        "Finalizado": "Finalizado",
                        "Próximamente": "Próximamente",
                    }

                    estado_original = anime.estado.strip()
                    estado_actual = (anime.estado_es or "").strip()

                    if not estado_actual or estado_actual == estado_original:
                        anime.estado_es = traducciones_estado.get(
                            estado_original,
                            traductor.translate(estado_original)
                        )
                        cambio = True
                        time.sleep(0.2)

                if cambio:
                    anime.save()
                    traducidos += 1
                    self.stdout.write(
                        self.style.SUCCESS(
                            f"Traducido: {anime.id} - {anime.titulo}"
                        )
                    )

            except Exception as e:
                errores += 1
                self.stdout.write(
                    self.style.ERROR(
                        f"Error en {anime.id} - {anime.titulo}: {e}"
                    )
                )
                time.sleep(1)
                continue

        pendientes_restantes = Anime.objects.filter(
            id__gte=desde,
            id__lte=hasta
        ).filter(
            Q(descripcion_es__isnull=True) |
            Q(descripcion_es="") |
            Q(descripcion_es=F("descripcion")) |
            Q(genero_es__isnull=True) |
            Q(genero_es="") |
            Q(genero_es=F("genero")) |
            Q(estado_es__isnull=True) |
            Q(estado_es="") |
            Q(estado_es=F("estado")) |
            Q(titulo_es__isnull=True) |
            Q(titulo_es="")
        ).count()

        self.stdout.write(self.style.SUCCESS("Ejecución terminada."))
        self.stdout.write(self.style.SUCCESS(f"Traducidos/corregidos: {traducidos}"))
        self.stdout.write(self.style.ERROR(f"Errores: {errores}"))
        self.stdout.write(
            self.style.WARNING(
                f"Pendientes restantes aproximados: {pendientes_restantes}"
            )
        )