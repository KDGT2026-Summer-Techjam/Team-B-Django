import secrets

from django.db import models

PUBLIC_ID_CHARS = "abcdefghjkmnpqrstuvwxyz23456789"
PUBLIC_ID_LENGTH = 6


def generate_public_id() -> str:
    return "".join(secrets.choice(PUBLIC_ID_CHARS) for _ in range(PUBLIC_ID_LENGTH))


def generate_edit_token() -> str:
    return secrets.token_urlsafe(16)


class Event(models.Model):
    public_id = models.CharField(
        max_length=PUBLIC_ID_LENGTH, unique=True, default=generate_public_id
    )
    title = models.CharField(max_length=255)
    event_date = models.DateField()
    location = models.CharField(max_length=255)
    organizer_name = models.CharField(max_length=255)
    edit_token = models.CharField(max_length=64, default=generate_edit_token)
    creator_visitor_id = models.CharField(max_length=64, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return self.title


class Participant(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="participants")
    name = models.CharField(max_length=255)
    visitor_id = models.CharField(max_length=64, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return self.name


class Mission(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="missions")
    order = models.PositiveIntegerField()
    prompt_text = models.CharField(max_length=255)
    # Base64エンコードした画像データをそのままDBに保存する（Renderの無料プランはディスクが永続化されないため）
    photo = models.TextField(blank=True, null=True)
    completed_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        ordering = ["order"]

    def __str__(self) -> str:
        return f"{self.event.title} - {self.prompt_text}"
