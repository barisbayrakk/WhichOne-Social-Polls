from django.contrib import admin
from .models import Poll, Choice, Vote


class ChoiceInline(admin.TabularInline):
    model = Choice
    extra = 2
    min_num = 2
    max_num = 5


@admin.register(Poll)
class PollAdmin(admin.ModelAdmin):
    list_display = ('question', 'author', 'is_active', 'total_votes', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('question', 'author__username')
    inlines = [ChoiceInline]


@admin.register(Vote)
class VoteAdmin(admin.ModelAdmin):
    list_display = ('user', 'poll', 'choice', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('user__username', 'poll__question')
