import time
import requests

from django.core.management.base import BaseCommand
from catalogo.models import Anime


class Command(BaseCommand):
    help = "Importa animes populares desde Jikan API"

    def handle(self, *args, **kwargs):
        total_importados = 0

        for page in range(1, 5):
            url = f"https://api.jikan.moe/v4/top/anime?page={page}"

            self.stdout.write(f"Importando página {page}...")

            response = requests.get(url)

            if response.status_code != 200:
                self.stdout.write(self.style.ERROR(f"Error en página {page}"))
                continue

            datos = response.json().get("data", [])

            for anime in datos:
                titulo = anime.get("title", "Sin título")
                descripcion = anime.get("synopsis") or "Sin descripción."
                imagen = anime["images"]["jpg"]["image_url"]

                temporada = anime.get("season") or "Desconocida"
                anio = anime.get("year") or 2000
                episodios = anime.get("episodes") or 0
                estado = anime.get("status") or "Desconocido"
                puntuacion = anime.get("score") or 0

                generos = ", ".join(
                    [g["name"] for g in anime.get("genres", [])]
                ) or "Sin género"

                Anime.objects.get_or_create(
                    titulo=titulo,
                    defaults={
                        "descripcion": descripcion,
                        "imagen": imagen,
                        "temporada": temporada,
                        "anio": anio,
                        "genero": generos,
                        "episodios": episodios,
                        "estado": estado,
                        "puntuacion": puntuacion,
                    }
                )

                total_importados += 1

            time.sleep(1)

        self.stdout.write(
            self.style.SUCCESS(
                f"Importación finalizada. Total procesados: {total_importados}"
            )
        )