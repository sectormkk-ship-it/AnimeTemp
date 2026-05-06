from django.contrib.auth.models import User

if not User.objects.filter(username="nico").exists():
    User.objects.create_superuser(
        username="nico",
        email="nico@gmail.com",
        password="NuevaPassword123"
    )
    print("Admin creado")
else:
    print("Ya existe")