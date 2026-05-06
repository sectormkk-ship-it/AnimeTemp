import requests
from datetime import datetime
from zoneinfo import ZoneInfo

from django.core.management.base import BaseCommand
from ...models import Anime


class Command(BaseCommand):
    help = "Importa animes en emisión desde AniList"

    def handle(self, *args, **kwargs):
        url = "https://graphql.anilist.co"

        query = """
        query ($page: Int) {
          Page(page: $page, perPage: 50) {
            pageInfo {
              hasNextPage
            }
            media(
              type: ANIME,
              status: RELEASING,
              isAdult: false,
              sort: POPULARITY_DESC
            ) {
              title {
                romaji
                english
              }
              description(asHtml: false)
              coverImage {
                large
              }
              season
              seasonYear
              genres
              episodes
              averageScore
              nextAiringEpisode {
                episode
                airingAt
              }
            }
          }
        }
        """

        total_importados = 0

        for page in range(1, 6):
            response = requests.post(
                url,
                json={
                    "query": query,
                    "variables": {
                        "page": page
                    }
                },
                timeout=20
            )

            data = response.json()

            if "data" not in data or data["data"] is None:
                self.stdout.write(
                    self.style.ERROR(
                        f"Error en página {page}: {data}"
                    )
                )
                continue

            animes = data["data"]["Page"]["media"]

            for item in animes:
                titulo = item["title"]["english"] or item["title"]["romaji"]
                descripcion = item["description"] or "Sin descripción disponible."
                imagen = item["coverImage"]["large"]
                temporada = item["season"] or "Desconocida"
                anio = item["seasonYear"] or datetime.now().year
                genero = ", ".join(item["genres"]) if item["genres"] else "Sin género"
                episodios = item["episodes"] or 0
                puntuacion = item["averageScore"] / 10 if item["averageScore"] else None

                proximo = item.get("nextAiringEpisode")

                if proximo:
                    fecha_arg = datetime.fromtimestamp(
                        proximo["airingAt"],
                        tz=ZoneInfo("America/Argentina/Buenos_Aires")
                    )
                    proximo_episodio = proximo["episode"]
                else:
                    fecha_arg = None
                    proximo_episodio = None

                Anime.objects.update_or_create(
                    titulo=titulo,
                    defaults={
                        "descripcion": descripcion,
                        "imagen": imagen,
                        "temporada": temporada,
                        "anio": anio,
                        "genero": genero,
                        "episodios": episodios,
                        "estado": "En emisión",
                        "puntuacion": puntuacion,
                        "proximo_episodio": proximo_episodio,
                        "fecha_emision": fecha_arg,
                    }
                )

                total_importados += 1

                if proximo:
                    self.stdout.write(
                        self.style.SUCCESS(
                            f"{titulo} - Episodio {proximo_episodio} - {fecha_arg.strftime('%d/%m/%Y %H:%M')} ARG"
                        )
                    )
                else:
                    self.stdout.write(
                        self.style.WARNING(
                            f"{titulo} importado sin próximo episodio"
                        )
                    )

        self.stdout.write(
            self.style.SUCCESS(
                f"Importación completada. Total de animes procesados: {total_importados}"
            )
        )