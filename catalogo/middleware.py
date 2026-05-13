from datetime import timedelta

from django.utils import timezone

from .models import PerfilUsuario


class ActualizarUltimoOnlineMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            perfil, creado = PerfilUsuario.objects.get_or_create(
                usuario=request.user
            )

            ahora = timezone.now()

            if (
                not perfil.ultimo_online
                or ahora - perfil.ultimo_online > timedelta(seconds=60)
            ):
                perfil.ultimo_online = ahora
                perfil.save(update_fields=["ultimo_online"])

        response = self.get_response(request)
        return response