import time
from django.core.management.base import BaseCommand
from deep_translator import GoogleTranslator
from catalogo.models import Anime


class Command(BaseCommand):
    help = "Traduce automáticamente solo descripciones que parecen estar en inglés"

    def add_arguments(self, parser):
        parser.add_argument("--desde", type=int, default=1)
        parser.add_argument("--hasta", type=int, default=999999)

    def parece_espanol(self, texto):
        if not texto:
            return False

        texto = texto.lower()

        palabras_es = [
            " el ", " la ", " los ", " las ", " un ", " una ",
            " de ", " del ", " que ", " en ", " y ", " por ",
            " para ", " con ", " como ", " pero ", " mientras ",
            " desde ", " hasta ", " cuando ", " donde ", " quien ",
            " su ", " sus ", " al ", " más ", " años ", " mundo ",
            " vida ", " historia ", " escuela ", " ciudad ",
        ]

        t = f" {texto} "

        return any(p in t for p in palabras_es) or any(c in texto for c in "áéíóúñ¿¡")

    def parece_ingles(self, texto):
        if not texto:
            return False

        texto = texto.lower()
        t = f" {texto} "

        palabras_en = [
            " the ", " a ", " an ", " and ", " or ", " but ",
            " in ", " on ", " at ", " from ", " with ", " without ",
            " after ", " before ", " while ", " when ", " where ",
            " who ", " his ", " her ", " their ", " this ", " that ",
            " is ", " are ", " was ", " were ", " has ", " have ",
            " begins ", " becomes ", " discovers ", " decides ",
            " school ", " world ", " life ", " story ", " battle ",
            " city ", " years ", " one day ",
        ]

        return any(p in t for p in palabras_en)

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
                f"Iniciando revisión del catálogo: {total} animes"
            )
        )

        for anime in animes:
            try:
                cambio = False

                descripcion_base = anime.descripcion or ""

                # Si la descripción original está en inglés, traducimos.
                # Si está en español, la dejamos como está.
                if descripcion_base and self.parece_ingles(descripcion_base) and not self.parece_espanol(descripcion_base):
                    texto = descripcion_base[:4500]
                    anime.descripcion_es = traductor.translate(texto)
                    cambio = True
                    time.sleep(0.4)

                elif descripcion_base and self.parece_espanol(descripcion_base):
                    if not anime.descripcion_es:
                        anime.descripcion_es = descripcion_base
                        cambio = True

                if anime.titulo and not anime.titulo_es:
                    anime.titulo_es = anime.titulo
                    cambio = True

                if anime.genero:
                    if not anime.genero_es or self.parece_ingles(anime.genero_es):
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

                    estado_es = traducciones_estado.get(anime.estado, anime.estado)

                    if not anime.estado_es or self.parece_ingles(anime.estado_es):
                        anime.estado_es = estado_es
                        cambio = True

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
                            f"Omitido español/listo: {anime.id} - {anime.titulo}"
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

        self.stdout.write(self.style.SUCCESS("Revisión terminada."))
        self.stdout.write(self.style.SUCCESS(f"Traducidos/corregidos: {traducidos}"))
        self.stdout.write(self.style.WARNING(f"Omitidos: {omitidos}"))
        self.stdout.write(self.style.ERROR(f"Errores: {errores}"))