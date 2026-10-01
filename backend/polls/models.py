from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError


from django.utils import timezone
from datetime import timedelta


class Poll(models.Model):
    DURATION_CHOICES = (
        (1, '1 Saat'),
        (6, '6 Saat'),
        (12, '12 Saat'),
        (24, '24 Saat'),
    )

    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='polls',
        verbose_name="Yazar"
    )
    question = models.CharField(max_length=300, verbose_name="Soru")
    is_active = models.BooleanField(default=True, verbose_name="Aktif mi?")
    expires_at = models.DateTimeField(null=True, blank=True, verbose_name="Bitiş Tarihi")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Oluşturulma Tarihi")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Güncellenme Tarihi")

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Anket"
        verbose_name_plural = "Anketler"

    def __str__(self):
        return self.question

    @property
    def total_votes(self):
        return sum(choice.votes for choice in self.choices.all())

    @property
    def is_expired(self):
        if self.expires_at:
            return timezone.now() > self.expires_at
        return False

    @property
    def is_open(self):
        return self.is_active and not self.is_expired

    @property
    def winning_choice_ids(self):
        if not self.total_votes or self.total_votes == 0:
            return []
        choices = list(self.choices.all())
        if not choices:
            return []
        max_votes = max(c.votes for c in choices)
        if max_votes == 0:
            return []
        return [c.id for c in choices if c.votes == max_votes]

    @property
    def has_winner(self):
        return len(self.winning_choice_ids) > 0

    @property
    def remaining_time_display(self):
        if not self.expires_at:
            return None
        now = timezone.now()
        if now >= self.expires_at:
            return "Süre doldu"
        diff = self.expires_at - now
        total_seconds = int(diff.total_seconds())
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        if hours > 0:
            return f"{hours} sa {minutes} dk kaldı"
        return f"{minutes} dk kaldı"

    def get_user_voted_choice_id(self, user):
        if user and user.is_authenticated:
            vote = self.user_votes.filter(user=user).first()
            if vote:
                return vote.choice_id
        return None


class Choice(models.Model):
    poll = models.ForeignKey(
        Poll,
        on_delete=models.CASCADE,
        related_name='choices',
        verbose_name="Anket"
    )
    text = models.CharField(max_length=200, verbose_name="Seçenek Metni")
    votes = models.PositiveIntegerField(default=0, verbose_name="Oy Sayısı")
    order = models.PositiveSmallIntegerField(default=0, verbose_name="Sıralama")

    class Meta:
        ordering = ['order', 'id']
        verbose_name = "Seçenek"
        verbose_name_plural = "Seçenekler"

    def __str__(self):
        return f"{self.poll.question[:30]}... -> {self.text}"

    @property
    def percentage(self):
        total = self.poll.total_votes
        if total > 0:
            return round((self.votes / total) * 100, 1)
        return 0.0

    @property
    def css_percentage(self):
        total = self.poll.total_votes
        if total > 0:
            val = round((self.votes / total) * 100, 1)
            return f"{val:.1f}".replace(',', '.')
        return "0.0"


class Vote(models.Model):
    poll = models.ForeignKey(
        Poll,
        on_delete=models.CASCADE,
        related_name='user_votes',
        verbose_name="Anket"
    )
    choice = models.ForeignKey(
        Choice,
        on_delete=models.CASCADE,
        related_name='user_votes',
        verbose_name="Seçilen Seçenek"
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='votes',
        verbose_name="Kullanıcı"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Oy Tarihi")

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['poll', 'user'], name='unique_user_poll_vote')
        ]
        verbose_name = "Kullanıcı Oyu"
        verbose_name_plural = "Kullanıcı Oyları"

    def __str__(self):
        return f"{self.user.username} -> {self.choice.text}"


class Bookmark(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='bookmarks',
        verbose_name="Kullanıcı"
    )
    poll = models.ForeignKey(
        Poll,
        on_delete=models.CASCADE,
        related_name='bookmarks',
        verbose_name="Anket"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Kayıt Tarihi")

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['user', 'poll'], name='unique_user_poll_bookmark')
        ]
        ordering = ['-created_at']
        verbose_name = "Kaydedilen Anket"
        verbose_name_plural = "Kaydedilen Anketler"

    def __str__(self):
        return f"{self.user.username} - {self.poll.question[:30]}"
