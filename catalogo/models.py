from django.db import models
from django.contrib.auth.models import User


# ============================================================
# PERFIL DE USUARIO
# ============================================================

class PerfilUsuario(models.Model):
    usuario = models.OneToOneField(User, on_delete=models.CASCADE)

    foto_perfil = models.ImageField(
        upload_to='perfiles/fotos/',
        blank=True,
        null=True
    )

    fondo_perfil = models.ImageField(
        upload_to='perfiles/fondos/',
        blank=True,
        null=True
    )

    bio = models.TextField(blank=True, null=True)

    genero_favorito = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )

    genero_no_recomendado = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )

    anime_favorito = models.CharField(
        max_length=200,
        blank=True,
        null=True
    )

    def __str__(self):
        return self.usuario.username


# ============================================================
# CATÁLOGO DE ANIME
# ============================================================

class Anime(models.Model):
    ESTADO_CHOICES = [
        ("En emisión", "En emisión"),
        ("Finalizado", "Finalizado"),
        ("Próximamente", "Próximamente"),
        ("Pausado", "Pausado"),
        ("Desconocido", "Desconocido"),
    ]

    mal_id = models.IntegerField(null=True, blank=True, unique=True)

    titulo = models.CharField(max_length=200)
    titulo_ingles = models.CharField(max_length=200, null=True, blank=True)
    titulo_japones = models.CharField(max_length=200, null=True, blank=True)

    descripcion = models.TextField(null=True, blank=True)
    imagen = models.URLField(null=True, blank=True)

    temporada = models.CharField(max_length=50, null=True, blank=True)
    anio = models.IntegerField(null=True, blank=True)
    genero = models.CharField(max_length=300, null=True, blank=True)
    tipo = models.CharField(max_length=50, null=True, blank=True)

    episodios = models.IntegerField(null=True, blank=True)
    proximo_episodio = models.IntegerField(null=True, blank=True)
    fecha_emision = models.DateTimeField(null=True, blank=True)

    estado = models.CharField(
        max_length=50,
        choices=ESTADO_CHOICES,
        default="Desconocido"
    )

    puntuacion = models.FloatField(null=True, blank=True)
    popularidad = models.IntegerField(null=True, blank=True)
    ranking = models.IntegerField(null=True, blank=True)

    trailer_url = models.URLField(null=True, blank=True)
    url_mal = models.URLField(null=True, blank=True)

    actualizado_en = models.DateTimeField(auto_now=True)
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-anio", "titulo"]
        verbose_name = "Anime"
        verbose_name_plural = "Animes"

    def __str__(self):
        return self.titulo

# ============================================================
# RESEÑAS DE ANIME
# ============================================================

class Resena(models.Model):
    usuario = models.ForeignKey(
        User,
        on_delete=models.CASCADE
    )

    anime = models.ForeignKey(
        Anime,
        on_delete=models.CASCADE,
        related_name="resenas"
    )

    texto = models.TextField()
    puntuacion = models.IntegerField(default=5)
    fecha = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("usuario", "anime")
        ordering = ["-fecha"]

    def __str__(self):
        return f"{self.usuario.username} - {self.anime.titulo}"


class LikeResena(models.Model):
    usuario = models.ForeignKey(
        User,
        on_delete=models.CASCADE
    )

    resena = models.ForeignKey(
        Resena,
        on_delete=models.CASCADE,
        related_name="likes"
    )

    fecha = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("usuario", "resena")

    def __str__(self):
        return f"{self.usuario.username} dio like a reseña {self.resena.id}"


# ============================================================
# FAVORITOS
# ============================================================

class Favorito(models.Model):
    usuario = models.ForeignKey(
        User,
        on_delete=models.CASCADE
    )

    anime = models.ForeignKey(
        Anime,
        on_delete=models.CASCADE
    )

    class Meta:
        unique_together = ('usuario', 'anime')

    def __str__(self):
        return f"{self.usuario.username} - {self.anime.titulo}"


# ============================================================
# SISTEMA DE AMISTAD
# ============================================================

class Amistad(models.Model):
    ESTADOS = (
        ("pendiente", "Pendiente"),
        ("aceptada", "Aceptada"),
        ("rechazada", "Rechazada"),
    )

    emisor = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="solicitudes_enviadas"
    )

    receptor = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="solicitudes_recibidas"
    )

    estado = models.CharField(
        max_length=20,
        choices=ESTADOS,
        default="pendiente"
    )

    fecha = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("emisor", "receptor")

    def __str__(self):
        return f"{self.emisor.username} → {self.receptor.username} ({self.estado})"


# ============================================================
# SISTEMA DE NOTIFICACIONES
# ============================================================

class Notificacion(models.Model):
    TIPOS = (
        ("amistad", "Solicitud de amistad"),
        ("strike", "Strike"),
        ("sistema", "Sistema"),
    )

    usuario = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="notificaciones"
    )

    tipo = models.CharField(max_length=20, choices=TIPOS)
    mensaje = models.CharField(max_length=255)

    solicitud = models.ForeignKey(
        Amistad,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="notificaciones"
    )

    leida = models.BooleanField(default=False)
    fecha = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-fecha"]

    def __str__(self):
        return f"{self.usuario.username} - {self.mensaje}"


# ============================================================
# CHAT PRIVADO
# ============================================================

class MensajePrivado(models.Model):
    remitente = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='mensajes_enviados'
    )

    destinatario = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='mensajes_recibidos'
    )

    mensaje = models.TextField()
    fecha = models.DateTimeField(auto_now_add=True)
    leido = models.BooleanField(default=False)

    class Meta:
        ordering = ['fecha']

    def __str__(self):
        return f"{self.remitente} -> {self.destinatario}"


# ============================================================
# USUARIOS SILENCIADOS
# ============================================================

class UsuarioSilenciado(models.Model):
    usuario = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="silenciador"
    )

    usuario_silenciado = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="silenciado"
    )

    fecha = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("usuario", "usuario_silenciado")


# ============================================================
# REPORTES GENERALES
# ============================================================

class Reporte(models.Model):
    TIPOS = (
        ("usuario", "Usuario"),
        ("bug", "Algo no funciona"),
        ("otro", "Otro"),
    )

    reportante = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="reportes_usuario_realizados"
    )

    usuario_reportado = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="reportes_usuario_recibidos",
        blank=True,
        null=True
    )

    tipo = models.CharField(max_length=20, choices=TIPOS)
    motivo = models.TextField(blank=True, null=True)
    fecha = models.DateTimeField(auto_now_add=True)
    revisado = models.BooleanField(default=False)

    class Meta:
        ordering = ["-fecha"]

    def __str__(self):
        return f"{self.reportante.username} reportó {self.tipo}"


# ============================================================
# REPORTES A USUARIOS
# ============================================================

class ReporteUsuario(models.Model):
    MOTIVOS = [
        ("spam", "Spam o publicidad"),
        ("acoso", "Acoso o insultos"),
        ("contenido", "Contenido inapropiado"),
        ("suplantacion", "Suplantación de identidad"),
        ("otro", "Otro"),
    ]

    reportante = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="reportes_realizados"
    )

    usuario_reportado = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="reportes_recibidos"
    )

    motivo = models.CharField(max_length=50, choices=MOTIVOS)
    descripcion = models.TextField(blank=True)
    fecha = models.DateTimeField(auto_now_add=True)
    revisado = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.reportante} reportó a {self.usuario_reportado}"


# ============================================================
# STRIKES / SANCIONES
# ============================================================

class StrikeUsuario(models.Model):
    usuario = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="strikes_recibidos"
    )

    admin = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="strikes_aplicados"
    )

    motivo = models.CharField(max_length=200)
    descripcion = models.TextField(blank=True)
    fecha = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Strike para {self.usuario.username} - {self.motivo}"