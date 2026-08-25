import secrets

from django.db import IntegrityError, models, transaction

PUBLIC_ID_CHARS = "abcdefghjkmnpqrstuvwxyz23456789"
PUBLIC_ID_LENGTH = 6
# 公開IDが衝突したときに生成し直す回数（docs/設計.md「ID生成のルール」）
PUBLIC_ID_MAX_ATTEMPTS = 5


class PublicIdCollisionError(Exception):
    """公開IDを規定回数生成し直しても重複が解消しなかったときに送出する。"""


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
    start_time = models.TimeField(blank=True, null=True)
    location = models.CharField(max_length=255)
    organizer_name = models.CharField(max_length=255)
    # Base64エンコードした画像データをそのままDBに保存する（Renderの無料プランはディスクが永続化されないため）
    image = models.TextField(blank=True, null=True)
    edit_token = models.CharField(max_length=64, default=generate_edit_token)
    creator_visitor_id = models.CharField(max_length=64, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return self.title

    def save(self, *args, **kwargs):
        """公開IDが衝突したら生成し直して保存する。

        UNIQUE制約に頼って衝突を検出する。保存前に存在確認するだけでは、
        確認から保存までの間に別のリクエストが同じIDを保存できてしまうため。
        """
        if not self._state.adding:
            return super().save(*args, **kwargs)

        for attempt in range(1, PUBLIC_ID_MAX_ATTEMPTS + 1):
            try:
                # IntegrityErrorが起きたトランザクションはそのまま継続できない
                with transaction.atomic():
                    return super().save(*args, **kwargs)
            except IntegrityError as error:
                # 公開ID以外の一意制約違反は、生成し直しても解消しない
                if "public_id" not in str(error):
                    raise
                if attempt == PUBLIC_ID_MAX_ATTEMPTS:
                    raise PublicIdCollisionError(
                        "公開IDが重複したため、イベントを保存できませんでした"
                    ) from error
                self.public_id = generate_public_id()


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
