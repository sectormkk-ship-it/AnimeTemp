import time
import requests

from django.core.management.base import BaseCommand
from catalogo.models import Anime


class Command(BaseCommand):
    help = "Importa catálogo general de animes populares desde Jikan API sin hentai"

    def add_arguments(self, parser):
        parser.add_argument(
            "--paginas",
            type=int,
            default=10,
            help="Cantidad de páginas a importar. Default: 10",
        )

    def handle(self, *args, **kwargs):
        paginas = kwargs["paginas"]

        creados = 0
        actualizados = 0
        omitidos = 0

        tipos_permitidos = ["TV", "Movie", "OVA", "ONA", "Special", "Music"]

        self.stdout.write(
            self.style.WARNING(f"Importando catálogo general: {paginas} páginas...")
        )

        for page in range(1, paginas + 1):
            url = f"https://api.jikan.moe/v4/top/anime?page={page}"

            self.stdout.write(self.style.WARNING(f"Importando página {page}..."))

            try:
                response = requests.get(url, timeout=20)

                if response.status_code == 429:
                    self.stdout.write(
                        self.style.WARNING("Rate limit detectado. Esperando 10 segundos...")
                    )
                    time.sleep(10)
                    response = requests.get(url, timeout=20)

                response.raise_for_status()

            except requests.RequestException as e:
                self.stdout.write(self.style.ERROR(f"Error en página {page}: {e}"))
                continue

            datos = response.json().get("data", [])

            for item in datos:
                mal_id = item.get("mal_id")

                if not mal_id:
                    omitidos += 1
                    continue

                titulo = (
                    item.get("title")
                    or item.get("title_english")
                    or item.get("title_japanese")
                    or "Sin título"
                )

                descripcion = item.get("synopsis") or "Sin descripción disponible."

                imagen = (
                    item.get("images", {})
                    .get("jpg", {})
                    .get("large_image_url")
                    or item.get("images", {})
                    .get("jpg", {})
                    .get("image_url")
                    or ""
                )

                temporada = item.get("season") or "Desconocida"
                anio = item.get("year") or 2000
                episodios = item.get("episodes")
                estado = item.get("status") or "Desconocido"
                puntuacion = item.get("score")

                generos = ", ".join(
                    genero.get("name", "")
                    for genero in item.get("genres", [])
                    if genero.get("name")
                ) or "Sin género"

                # No importar hentai
                if "hentai" in generos.lower():
                    omitidos += 1
                    continue

                tipo = item.get("type")

                if tipo not in tipos_permitidos:
                    omitidos += 1
                    continue

                titulo_ingles = item.get("title_english") or ""
                titulo_japones = item.get("title_japanese") or ""
                popularidad = item.get("popularity")
                ranking = item.get("rank")
                url_mal = item.get("url") or ""
                trailer_url = item.get("trailer", {}).get("url") or ""

                anime, creado = Anime.objects.update_or_create(
                    mal_id=mal_id,
                    defaults={
                        "titulo": titulo,
                        "titulo_ingles": titulo_ingles,
                        "titulo_japones": titulo_japones,
                        "descripcion": descripcion,
                        "imagen": imagen,
                        "temporada": temporada,
                        "anio": anio,
                        "genero": generos,
                        "tipo": tipo,
                        "episodios": episodios,
                        "estado": estado,
                        "puntuacion": puntuacion,
                        "popularidad": popularidad,
                        "ranking": ranking,
                        "trailer_url": trailer_url,
                        "url_mal": url_mal,
                    },
                )

                if creado:
                    creados += 1
                    self.stdout.write(self.style.SUCCESS(f"Nuevo: {titulo}"))
                else:
                    actualizados += 1

            time.sleep(1.2)

        self.stdout.write(self.style.SUCCESS("Importación general terminada."))
        self.stdout.write(self.style.SUCCESS(f"Creados: {creados}"))
        self.stdout.write(self.style.SUCCESS(f"Actualizados: {actualizados}"))
        self.stdout.write(self.style.WARNING(f"Omitidos: {omitidos}"))