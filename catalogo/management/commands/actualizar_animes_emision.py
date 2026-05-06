import time
import requests

from datetime import timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
from catalogo.models import Anime


class Command(BaseCommand):
    help = "Actualiza automáticamente los animes en emisión desde Jikan API"

    def obtener_fecha_emision(self, item):
        broadcast = item.get("broadcast") or {}

        dia = broadcast.get("day")
        hora = broadcast.get("time")

        dias_map = {
            "Mondays": 0,
            "Tuesdays": 1,
            "Wednesdays": 2,
            "Thursdays": 3,
            "Fridays": 4,
            "Saturdays": 5,
            "Sundays": 6,
        }

        if not dia or not hora or dia not in dias_map:
            return None

        try:
            hora_partes = hora.split(":")
            hora_num = int(hora_partes[0])
            minuto_num = int(hora_partes[1])
        except Exception:
            return None

        ahora = timezone.now()
        dia_objetivo = dias_map[dia]
        dias_hasta = dia_objetivo - ahora.weekday()

        if dias_hasta < 0:
            dias_hasta += 7

        fecha = ahora + timedelta(days=dias_hasta)

        fecha = fecha.replace(
            hour=hora_num,
            minute=minuto_num,
            second=0,
            microsecond=0,
        )

        if fecha < ahora:
            fecha += timedelta(days=7)

        return fecha

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.WARNING("Actualizando animes en emisión..."))

        pagina = 1
        creados = 0
        actualizados = 0
        nuevos_episodios = 0

        while True:
            url = f"https://api.jikan.moe/v4/seasons/now?page={pagina}"

            try:
                response = requests.get(url, timeout=20)

                if response.status_code == 429:
                    self.stdout.write(
                        self.style.WARNING("Rate limit detectado. Esperando 10 segundos...")
                    )
                    time.sleep(10)
                    continue

                response.raise_for_status()

            except requests.RequestException as e:
                self.stdout.write(self.style.ERROR(f"Error conectando con Jikan: {e}"))
                break

            data = response.json()
            animes = data.get("data", [])

            if not animes:
                break

            for item in animes:
                mal_id = item.get("mal_id")

                if not mal_id:
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

                temporada = item.get("season") or "Actual"
                anio = item.get("year")

                generos = ", ".join(
                    genero.get("name", "")
                    for genero in item.get("genres", [])
                    if genero.get("name")
                )

                # FILTRO HENTAI
                if "hentai" in generos.lower():
                    continue

                tipo = item.get("type")

                # FILTRO DE TIPOS PERMITIDOS
                if tipo not in ["TV", "ONA", "OVA", "Music"]:
                    continue

                episodios_api = item.get("episodes")
                puntuacion = item.get("score")

                titulo_ingles = item.get("title_english") or ""
                titulo_japones = item.get("title_japanese") or ""
                popularidad = item.get("popularity")
                ranking = item.get("rank")
                url_mal = item.get("url") or ""

                trailer_url = item.get("trailer", {}).get("url") or ""

                fecha_emision = self.obtener_fecha_emision(item)

                anime_existente = Anime.objects.filter(mal_id=mal_id).first()

                if anime_existente:
                    if (
                        episodios_api is not None
                        and anime_existente.episodios is not None
                        and episodios_api > anime_existente.episodios
                    ):
                        nuevos_episodios += 1
                        self.stdout.write(
                            self.style.SUCCESS(
                                f"Nuevo episodio detectado: {titulo} "
                                f"({anime_existente.episodios} -> {episodios_api})"
                            )
                        )

                    anime_existente.titulo = titulo
                    anime_existente.titulo_ingles = titulo_ingles
                    anime_existente.titulo_japones = titulo_japones
                    anime_existente.descripcion = descripcion
                    anime_existente.imagen = imagen
                    anime_existente.temporada = temporada
                    anime_existente.anio = anio
                    anime_existente.genero = generos
                    anime_existente.tipo = tipo
                    anime_existente.episodios = episodios_api
                    anime_existente.estado = "En emisión"
                    anime_existente.puntuacion = puntuacion
                    anime_existente.popularidad = popularidad
                    anime_existente.ranking = ranking
                    anime_existente.trailer_url = trailer_url
                    anime_existente.url_mal = url_mal

                    if fecha_emision:
                        anime_existente.fecha_emision = fecha_emision

                    if episodios_api:
                        anime_existente.proximo_episodio = episodios_api + 1

                    anime_existente.save()
                    actualizados += 1

                else:
                    Anime.objects.create(
                        mal_id=mal_id,
                        titulo=titulo,
                        titulo_ingles=titulo_ingles,
                        titulo_japones=titulo_japones,
                        descripcion=descripcion,
                        imagen=imagen,
                        temporada=temporada,
                        anio=anio,
                        genero=generos,
                        tipo=tipo,
                        episodios=episodios_api,
                        estado="En emisión",
                        puntuacion=puntuacion,
                        popularidad=popularidad,
                        ranking=ranking,
                        trailer_url=trailer_url,
                        url_mal=url_mal,
                        fecha_emision=fecha_emision,
                        proximo_episodio=(episodios_api + 1) if episodios_api else None,
                    )

                    creados += 1
                    self.stdout.write(
                        self.style.SUCCESS(f"Nuevo anime agregado: {titulo}")
                    )

            pagination = data.get("pagination", {})
            has_next_page = pagination.get("has_next_page", False)

            if not has_next_page:
                break

            pagina += 1
            time.sleep(1.2)

        self.stdout.write(self.style.SUCCESS("Actualización terminada."))
        self.stdout.write(self.style.SUCCESS(f"Nuevos animes: {creados}"))
        self.stdout.write(self.style.SUCCESS(f"Actualizados: {actualizados}"))
        self.stdout.write(
            self.style.SUCCESS(f"Nuevos episodios detectados: {nuevos_episodios}")
        )