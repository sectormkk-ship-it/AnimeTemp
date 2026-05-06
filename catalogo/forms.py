from django import forms
from .models import PerfilUsuario, Resena


class PerfilUsuarioForm(forms.ModelForm):
    borrar_foto = forms.BooleanField(required=False)
    borrar_fondo = forms.BooleanField(required=False)

    class Meta:
        model = PerfilUsuario
        fields = [
            'foto_perfil',
            'fondo_perfil',
            'bio',
            'genero_favorito',
            'genero_no_recomendado',
            'anime_favorito',
        ]

        widgets = {
            'bio': forms.Textarea(attrs={
                'placeholder': 'Escribí algo sobre vos...'
            }),
            'genero_favorito': forms.TextInput(attrs={
                'placeholder': 'Ej: Acción, Romance, Fantasía'
            }),
            'genero_no_recomendado': forms.TextInput(attrs={
                'placeholder': 'Ej: Terror, Gore'
            }),
            'anime_favorito': forms.TextInput(attrs={
                'placeholder': 'Ej: Bleach, Naruto, Soul Eater'
            }),
        }


class ResenaForm(forms.ModelForm):
    class Meta:
        model = Resena
        fields = ['texto', 'puntuacion']

        widgets = {
            'texto': forms.Textarea(attrs={
                'rows': 4,
                'placeholder': 'Escribe tu reseña...'
            }),
            'puntuacion': forms.NumberInput(attrs={
                'min': 1,
                'max': 10
            }),
        }