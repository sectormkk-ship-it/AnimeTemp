import requests
import time

from django.core.management.base import BaseCommand
from catalogo.models import Anime


class Command(BaseCommand):
    help = "Elimina animes adultos/hentai importados desde AniList"

    def handle(self, *args, **kwargs):
        url = "https://graphql.anilist.co"

        query = """
        query ($search: String) {
          Media(search: $search, type: ANIME) {
            title {
              romaji
              english
            }
            isAdult
            genres
          }
        }
        """

        total_revisados = 0
        total_eliminados = 0

        palabras_bloqueadas = [
            "hentai",
            "adult",
            "erotic",
            "ecchi",
            "rx",
            "r18",
            "18+",
            "sex",
            "porn",
        ]

        animes = Anime.objects.all()

        for anime in animes:
            total_revisados += 1
            borrar = False
            motivo = ""

            texto_local = f"{anime.titulo} {anime.genero}".lower()

            if any(palabra in texto_local for palabra in palabras_bloqueadas):
                borrar = True
                motivo = "palabra bloqueada local"

            if not borrar:
                try:
                    response = requests.post(
                        url,
                        json={
                            "query": query,
                            "variables": {
                                "search": anime.titulo
                            }
                        },
                        timeout=10
                    )

                    data = response.json()

                    if data.get("errors"):
                        self.stdout.write(
                            self.style.WARNING(
                                f"No se pudo revisar en AniList: {anime.titulo}"
                            )
                        )
                        media = None
                    else:
                        data_section = data.get("data") or {}
                        media = data_section.get("Media")

                    if media:
                        if media.get("isAdult"):
                            borrar = True
                            motivo = "AniList isAdult=True"

                        generos = media.get("genres") or []

                        if any(
                            g.lower() in ["hentai", "ecchi"]
                            for g in generos
                        ):
                            borrar = True
                            motivo = f"género adulto AniList: {generos}"

                except Exception as e:
                    self.stdout.write(
                        self.style.WARNING(
                            f"Error revisando {anime.titulo}: {str(e)}"
                        )
                    )

            if borrar:
                self.stdout.write(
                    self.style.WARNING(
                        f"Eliminando: {anime.titulo} | Motivo: {motivo}"
                    )
                )
                anime.delete()
                total_eliminados += 1
            else:
                self.stdout.write(
                    self.style.SUCCESS(
                        f"OK: {anime.titulo}"
                    )
                )

            time.sleep(0.5)

        self.stdout.write(
            self.style.SUCCESS(
                f"Limpieza terminada. Revisados: {total_revisados} | Eliminados: {total_eliminados}"
            )
        )