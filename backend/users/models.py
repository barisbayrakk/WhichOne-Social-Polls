from django.contrib.auth.models import AbstractUser
from django.db import models


class CustomUser(AbstractUser):
    email = models.EmailField(
        unique=True,
        blank=False,
        error_messages={
            'unique': 'Bu e-posta adresi ile zaten kayıtlı bir hesap var.',
        },
        verbose_name="E-posta"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Kayıt Tarihi")

    REQUIRED_FIELDS = ['email']

    class Meta:
        verbose_name = 'Kullanıcı'
        verbose_name_plural = 'Kullanıcılar'

    def __str__(self):
        return self.username
