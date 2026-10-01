from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import RegisterForm, LoginForm
from .models import CustomUser
from polls.models import Poll, Bookmark, Vote


def register_view(request):
    if request.user.is_authenticated:
        return redirect('polls:feed')

    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f"Hoş geldin, {user.username}! Hesabın başarıyla oluşturuldu.")
            return redirect('polls:feed')
        else:
            messages.error(request, "Lütfen formdaki hataları düzeltin.")
    else:
        form = RegisterForm()

    return render(request, 'users/register.html', {'form': form})


def login_view(request):
    if request.user.is_authenticated:
        return redirect('polls:feed')

    if request.method == 'POST':
        post_data = request.POST.copy()
        username_or_email = post_data.get('username', '').strip()
        if '@' in username_or_email:
            user_found = CustomUser.objects.filter(email__iexact=username_or_email).first()
            if user_found:
                post_data['username'] = user_found.username

        form = LoginForm(request, data=post_data)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f"Tekrar hoş geldin, {user.username}!")
            next_url = request.GET.get('next', 'polls:feed')
            return redirect(next_url)
        else:
            messages.error(request, "Geçersiz kullanıcı adı/e-posta veya parola.")
    else:
        form = LoginForm()

    return render(request, 'users/login.html', {'form': form})


def logout_view(request):
    logout(request)
    request.session.flush()
    messages.info(request, "Başarıyla çıkış yaptınız.")
    return redirect('polls:feed')


@login_required
def profile_view(request):
    user_polls = Poll.objects.filter(author=request.user).prefetch_related('choices').order_by('-created_at')
    total_polls = user_polls.count()
    active_polls_count = sum(1 for p in user_polls if p.is_open)
    closed_polls_count = total_polls - active_polls_count
    total_votes_received = sum(p.total_votes for p in user_polls)

    bookmarks = Bookmark.objects.filter(user=request.user).select_related('poll__author').prefetch_related('poll__choices')
    bookmarked_polls = [b.poll for b in bookmarks]
    bookmarked_poll_ids = {p.id for p in bookmarked_polls}

    if bookmarked_polls:
        b_votes = Vote.objects.filter(user=request.user, poll__in=bookmarked_polls).values('poll_id', 'choice_id')
        b_voted_map = {uv['poll_id']: uv['choice_id'] for uv in b_votes}
        for bp in bookmarked_polls:
            bp.user_choice_id = b_voted_map.get(bp.id)
            bp.has_user_voted = bool(bp.user_choice_id)
            bp.is_bookmarked = True

    for p in user_polls:
        p.is_bookmarked = p.id in bookmarked_poll_ids

    total_bookmarks = len(bookmarked_polls)

    context = {
        'polls': user_polls,
        'total_polls': total_polls,
        'active_polls_count': active_polls_count,
        'closed_polls_count': closed_polls_count,
        'total_votes_received': total_votes_received,
        'bookmarked_polls': bookmarked_polls,
        'total_bookmarks': total_bookmarks,
    }
    return render(request, 'users/profile.html', context)
