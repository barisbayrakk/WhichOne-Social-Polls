import json
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponseForbidden
from django.views.decorators.http import require_POST
from django.contrib import messages
from datetime import timedelta
from django.utils import timezone
from django.db.models import F, Sum
from django.db.models.functions import Coalesce
from .models import Poll, Choice, Vote, Bookmark
from .forms import PollCreateForm


def feed_view(request):
    sort = request.GET.get('sort', 'latest')
    
    base_qs = Poll.objects.filter(is_active=True).prefetch_related('choices', 'user_votes').select_related('author')
    
    if sort == 'popular':
        polls = base_qs.annotate(
            total_vote_count=Coalesce(Sum('choices__votes'), 0)
        ).order_by('-total_vote_count', '-created_at')
    else:
        sort = 'latest'
        polls = base_qs.order_by('-created_at')
    
    voted_map = {}
    bookmarked_poll_ids = set()
    if request.user.is_authenticated:
        user_votes = Vote.objects.filter(user=request.user, poll__in=polls).values('poll_id', 'choice_id')
        voted_map = {uv['poll_id']: uv['choice_id'] for uv in user_votes}
        bookmarked_poll_ids = set(Bookmark.objects.filter(user=request.user, poll__in=polls).values_list('poll_id', flat=True))
    else:
        for poll in polls:
            guest_vote = request.session.get(f'voted_poll_{poll.id}')
            if guest_vote:
                voted_map[poll.id] = guest_vote

    for poll in polls:
        if request.user.is_authenticated:
            poll.user_choice_id = voted_map.get(poll.id)
            poll.is_bookmarked = poll.id in bookmarked_poll_ids
        else:
            poll.user_choice_id = request.session.get(f'voted_poll_{poll.id}')
            poll.is_bookmarked = False
        poll.has_user_voted = bool(poll.user_choice_id)

    context = {
        'polls': polls,
        'current_sort': sort,
    }
    return render(request, 'polls/feed.html', context)


def poll_detail_view(request, poll_id):
    poll = get_object_or_404(Poll.objects.prefetch_related('choices').select_related('author'), id=poll_id)
    
    user_choice_id = None
    is_bookmarked = False
    if request.user.is_authenticated:
        user_choice_id = poll.get_user_voted_choice_id(request.user)
        is_bookmarked = Bookmark.objects.filter(user=request.user, poll=poll).exists()
    if not user_choice_id:
        user_choice_id = request.session.get(f'voted_poll_{poll.id}')

    context = {
        'poll': poll,
        'user_choice_id': user_choice_id,
        'is_bookmarked': is_bookmarked,
    }
    return render(request, 'polls/poll_detail.html', context)


@login_required
def poll_create_view(request):
    if request.method == 'POST':
        form = PollCreateForm(request.POST)
        raw_choices = request.POST.getlist('choices')
        cleaned_choices = [c.strip() for c in raw_choices if c and c.strip()]

        if len(cleaned_choices) < 2:
            messages.error(request, "Bir anket en az 2 seçenek içermelidir.")
        elif len(cleaned_choices) > 5:
            messages.error(request, "Bir anket en fazla 5 seçenek içerebilir.")
        elif form.is_valid():
            poll = form.save(commit=False)
            poll.author = request.user
            duration_hours = form.cleaned_data.get('duration', 24)
            poll.expires_at = timezone.now() + timedelta(hours=int(duration_hours))
            poll.save()

            for order, text in enumerate(cleaned_choices):
                Choice.objects.create(
                    poll=poll,
                    text=text,
                    order=order
                )

            messages.success(request, "Anketiniz başarıyla oluşturuldu.")
            return redirect('polls:poll_detail', poll_id=poll.id)
    else:
        form = PollCreateForm()
        cleaned_choices = []

    return render(request, 'polls/poll_create.html', {
        'form': form,
        'initial_choices': cleaned_choices or ['', '']
    })


@require_POST
def vote_api(request, poll_id):
    poll = get_object_or_404(Poll, id=poll_id)

    if not poll.is_open:
        return JsonResponse({'success': False, 'error': 'Bu anket oylamaya kapatılmıştır veya süresi dolmuştur.'}, status=400)

    choice_id = None
    if request.content_type == 'application/json':
        try:
            data = json.loads(request.body)
            choice_id = data.get('choice_id')
        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'error': 'Geçersiz veri formatı.'}, status=400)
    else:
        choice_id = request.POST.get('choice_id')

    if not choice_id:
        return JsonResponse({'success': False, 'error': 'Lütfen bir seçenek belirtin.'}, status=400)

    try:
        choice = poll.choices.get(id=choice_id)
    except Choice.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Geçersiz seçenek seçildi.'}, status=400)

    if request.user.is_authenticated:
        if Vote.objects.filter(poll=poll, user=request.user).exists():
            return JsonResponse({'success': False, 'error': 'Bu ankete daha önce oy kullandınız.'}, status=400)

        try:
            Vote.objects.create(poll=poll, choice=choice, user=request.user)
        except Exception:
            return JsonResponse({'success': False, 'error': 'Bu ankete daha önce oy kullandınız.'}, status=400)
    else:
        session_key = f'voted_poll_{poll.id}'
        if request.session.get(session_key):
            return JsonResponse({'success': False, 'error': 'Bu ankete daha önce oy kullandınız.'}, status=400)
        request.session[session_key] = choice.id
        request.session.modified = True

    Choice.objects.filter(id=choice.id).update(votes=F('votes') + 1)

    poll.refresh_from_db()
    choices = poll.choices.all()
    total_votes = sum(c.votes for c in choices)

    choices_data = []
    for c in choices:
        pct = round((c.votes / total_votes * 100), 1) if total_votes > 0 else 0.0
        choices_data.append({
            'id': c.id,
            'text': c.text,
            'votes': c.votes,
            'percentage': pct
        })

    return JsonResponse({
        'success': True,
        'poll_id': poll.id,
        'selected_choice_id': choice.id,
        'is_authenticated': request.user.is_authenticated,
        'total_votes': total_votes,
        'choices': choices_data,
        'message': 'Oyunuz başarıyla kaydedildi!'
    })


@login_required
@require_POST
def poll_toggle_active(request, poll_id):
    poll = get_object_or_404(Poll, id=poll_id)
    if poll.author != request.user:
        return HttpResponseForbidden("Bu işlem için yetkiniz yok.")
    
    poll.is_active = not poll.is_active
    poll.save()
    status_text = "oylamaya açıldı" if poll.is_active else "oylamaya kapatıldı"
    messages.success(request, f"Anket {status_text}.")
    next_url = request.POST.get('next')
    if next_url:
        return redirect(next_url)
    return redirect('polls:poll_detail', poll_id=poll.id)


@login_required
@require_POST
def poll_delete(request, poll_id):
    poll = get_object_or_404(Poll, id=poll_id)
    if poll.author != request.user:
        return HttpResponseForbidden("Bu işlem için yetkiniz yok.")
    
    poll.delete()
    messages.success(request, "Anket başarıyla silindi.")
    next_url = request.POST.get('next')
    if next_url:
        return redirect(next_url)
    return redirect('polls:feed')


@login_required
@require_POST
def bookmark_api(request, poll_id):
    poll = get_object_or_404(Poll, id=poll_id)
    bookmark = Bookmark.objects.filter(user=request.user, poll=poll).first()
    if bookmark:
        bookmark.delete()
        bookmarked = False
        message = "Anket kaydedilenlerden çıkarıldı."
    else:
        Bookmark.objects.create(user=request.user, poll=poll)
        bookmarked = True
        message = "Anket kaydedilenlere eklendi!"

    return JsonResponse({
        'success': True,
        'poll_id': poll.id,
        'bookmarked': bookmarked,
        'message': message
    })
