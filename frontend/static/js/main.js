document.addEventListener('DOMContentLoaded', () => {
    initThemeToggle();
    initVoting();
    initShareButtons();
    initDynamicChoices();
    initAlertDismiss();
    initLogoutCleanup();
    restoreLocalStorageVotes();
    initCountdownTimers();
    initBookmarks();
});

function initThemeToggle() {
    const toggleBtn = document.getElementById('theme-toggle-btn');
    if (!toggleBtn) return;

    toggleBtn.addEventListener('click', () => {
        const isDark = document.documentElement.getAttribute('data-theme') === 'dark';
        if (isDark) {
            document.documentElement.removeAttribute('data-theme');
            localStorage.setItem('hangisi_theme', 'light');
        } else {
            document.documentElement.setAttribute('data-theme', 'dark');
            localStorage.setItem('hangisi_theme', 'dark');
        }
    });
}

function initLogoutCleanup() {
    const logoutBtn = document.getElementById('btn-header-logout');
    if (logoutBtn) {
        // If logged in, clear any old guest votes from local storage
        localStorage.removeItem('hangisi_voted_polls');
        const form = logoutBtn.closest('form');
        if (form) {
            form.addEventListener('submit', () => {
                localStorage.removeItem('hangisi_voted_polls');
            });
        }
    }
}

function showToast(message, duration = 3000) {
    let toast = document.getElementById('global-toast');
    if (!toast) {
        toast = document.createElement('div');
        toast.id = 'global-toast';
        toast.className = 'toast';
        document.body.appendChild(toast);
    }
    toast.textContent = message;
    toast.classList.add('show');
    setTimeout(() => {
        toast.classList.remove('show');
    }, duration);
}

function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

function getStoredVote(pollId) {
    try {
        const votes = JSON.parse(localStorage.getItem('hangisi_voted_polls') || '{}');
        return votes[pollId] || null;
    } catch (e) {
        return null;
    }
}

function saveStoredVote(pollId, choiceId) {
    try {
        const votes = JSON.parse(localStorage.getItem('hangisi_voted_polls') || '{}');
        votes[pollId] = choiceId;
        localStorage.setItem('hangisi_voted_polls', JSON.stringify(votes));
    } catch (e) {
        console.error(e);
    }
}

function restoreLocalStorageVotes() {
    document.querySelectorAll('.poll-card').forEach(card => {
        const pollId = card.dataset.pollId;
        if (!pollId) return;

        const storedChoiceId = getStoredVote(pollId);
        if (storedChoiceId) {
            card.classList.add('has-voted', 'show-results');
            const choiceItem = card.querySelector(`[data-choice-id="${storedChoiceId}"]`);
            if (choiceItem && !choiceItem.classList.contains('selected')) {
                choiceItem.classList.add('selected');
            }
        }
    });
}

function initVoting() {
    document.addEventListener('click', async (e) => {
        const choiceItem = e.target.closest('.choice-item');
        if (!choiceItem) return;

        const pollCard = choiceItem.closest('.poll-card');
        if (!pollCard) return;

        const pollId = pollCard.dataset.pollId;
        const choiceId = choiceItem.dataset.choiceId;

        if (pollCard.classList.contains('has-voted') || pollCard.classList.contains('is-closed')) {
            showToast('Bu ankete zaten oy kullandınız.');
            return;
        }

        choiceItem.style.opacity = '0.7';

        try {
            const csrfToken = getCookie('csrftoken');
            const response = await fetch(`/api/poll/${pollId}/vote/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken || '',
                },
                body: JSON.stringify({ choice_id: choiceId })
            });

            const data = await response.json();

            if (data.success) {
                if (!data.is_authenticated) {
                    saveStoredVote(pollId, choiceId);
                }

                pollCard.classList.add('has-voted', 'show-results');
                choiceItem.classList.add('selected');

                const totalVotesEl = pollCard.querySelector('.poll-total-votes-count');
                if (totalVotesEl) {
                    totalVotesEl.textContent = `${data.total_votes} oy`;
                }

                data.choices.forEach(ch => {
                    const chRow = pollCard.querySelector(`[data-choice-id="${ch.id}"]`);
                    if (chRow) {
                        chRow.setAttribute('data-votes', ch.votes);
                        const progressBg = chRow.querySelector('.choice-progress-bg');
                        const pctEl = chRow.querySelector('.choice-percentage');
                        const votesCountEl = chRow.querySelector('.choice-votes-count');

                        if (progressBg) {
                            progressBg.style.width = `${ch.percentage}%`;
                        }
                        if (pctEl) {
                            pctEl.textContent = `%${ch.percentage}`;
                        }
                        if (votesCountEl) {
                            votesCountEl.textContent = `(${ch.votes} oy)`;
                        }
                    }
                });

                showToast(data.message || 'Oyunuz başarıyla kaydedildi!');
            } else {
                showToast(data.error || 'Oy verilirken bir sorun oluştu.');
            }
        } catch (err) {
            console.error(err);
            showToast('Bağlantı hatası oluştu, lütfen tekrar deneyin.');
        } finally {
            choiceItem.style.opacity = '1';
        }
    });
}

function initShareButtons() {
    document.addEventListener('click', (e) => {
        const shareBtn = e.target.closest('.btn-share');
        if (!shareBtn) return;

        const shareUrl = shareBtn.dataset.url || window.location.href;

        if (navigator.clipboard && navigator.clipboard.writeText) {
            navigator.clipboard.writeText(shareUrl).then(() => {
                showToast('Anket bağlantısı panoya kopyalandı!');
            }).catch(() => {
                fallbackCopy(shareUrl);
            });
        } else {
            fallbackCopy(shareUrl);
        }
    });
}

function fallbackCopy(text) {
    const textArea = document.createElement("textarea");
    textArea.value = text;
    textArea.style.position = "fixed";
    textArea.style.left = "-999999px";
    document.body.appendChild(textArea);
    textArea.focus();
    textArea.select();
    try {
        document.execCommand('copy');
        showToast('Anket bağlantısı panoya kopyalandı!');
    } catch (err) {
        showToast('Bağlantı: ' + text);
    }
    document.body.removeChild(textArea);
}

function initDynamicChoices() {
    const container = document.getElementById('dynamic-choices-container');
    const addBtn = document.getElementById('btn-add-choice');
    if (!container || !addBtn) return;

    const MIN_CHOICES = 2;
    const MAX_CHOICES = 5;

    function updateRowIndicators() {
        const rows = container.querySelectorAll('.choice-input-row');
        rows.forEach((row, index) => {
            const badge = row.querySelector('.choice-order-badge');
            if (badge) {
                badge.textContent = index + 1;
            }
            const removeBtn = row.querySelector('.btn-remove-choice');
            if (removeBtn) {
                removeBtn.style.display = rows.length > MIN_CHOICES ? 'flex' : 'none';
            }
        });

        if (rows.length >= MAX_CHOICES) {
            addBtn.style.display = 'none';
        } else {
            addBtn.style.display = 'inline-flex';
        }
    }

    addBtn.addEventListener('click', () => {
        const rows = container.querySelectorAll('.choice-input-row');
        if (rows.length >= MAX_CHOICES) return;

        const newIndex = rows.length + 1;
        const newRow = document.createElement('div');
        newRow.className = 'choice-input-row';
        newRow.innerHTML = `
            <span class="choice-order-badge">${newIndex}</span>
            <input type="text" name="choices" class="form-input" placeholder="Seçenek ${newIndex}" required maxlength="200" autocomplete="off">
            <button type="button" class="btn-remove-choice" title="Seçeneği Sil">✕</button>
        `;
        container.appendChild(newRow);
        newRow.querySelector('input').focus();
        updateRowIndicators();
    });

    container.addEventListener('click', (e) => {
        const removeBtn = e.target.closest('.btn-remove-choice');
        if (!removeBtn) return;

        const rows = container.querySelectorAll('.choice-input-row');
        if (rows.length <= MIN_CHOICES) return;

        const row = removeBtn.closest('.choice-input-row');
        row.remove();
        updateRowIndicators();
    });

    updateRowIndicators();
}

function initAlertDismiss() {
    document.addEventListener('click', (e) => {
        const closeBtn = e.target.closest('.alert-close');
        if (!closeBtn) return;
        const alert = closeBtn.closest('.alert');
        if (alert) {
            alert.remove();
        }
    });
}

function formatTimeRemaining(diffMs) {
    if (diffMs <= 0) return 'Süre doldu';
    const totalSeconds = Math.floor(diffMs / 1000);
    const days = Math.floor(totalSeconds / 86400);
    const hours = Math.floor((totalSeconds % 86400) / 3600);
    const minutes = Math.floor((totalSeconds % 3600) / 60);
    const seconds = totalSeconds % 60;

    if (days > 0) {
        return `${days} gün ${hours} sa kaldı`;
    }
    if (hours > 0) {
        return `${hours} sa ${minutes} dk ${seconds} sn kaldı`;
    }
    if (minutes > 0) {
        return `${minutes} dk ${seconds} sn kaldı`;
    }
    return `${seconds} sn kaldı`;
}

function initCountdownTimers() {
    function updateTimers() {
        const timerElements = document.querySelectorAll('[data-expires-at]');
        const now = new Date().getTime();

        timerElements.forEach(el => {
            const expireStr = el.getAttribute('data-expires-at');
            if (!expireStr) return;

            const expireTime = new Date(expireStr).getTime();
            if (isNaN(expireTime)) return;

            const diff = expireTime - now;
            if (diff <= 0) {
                el.textContent = 'Süre Doldu';
                el.classList.remove('poll-status-active');
                el.classList.add('poll-status-closed');
                el.removeAttribute('data-expires-at');

                const card = el.closest('.poll-card');
                if (card) {
                    card.classList.add('is-closed', 'show-results');
                    highlightClosedPollWinners(card);
                }
            } else {
                el.textContent = formatTimeRemaining(diff);
            }
        });
    }

    updateTimers();
    setInterval(updateTimers, 1000);
}

function highlightClosedPollWinners(card) {
    if (!card) return;
    const choiceItems = card.querySelectorAll('.choice-item');
    if (!choiceItems.length) return;

    let maxVotes = -1;
    choiceItems.forEach(item => {
        const votes = parseInt(item.getAttribute('data-votes') || '0', 10);
        if (votes > maxVotes) {
            maxVotes = votes;
        }
    });

    if (maxVotes <= 0) return;

    choiceItems.forEach(item => {
        const votes = parseInt(item.getAttribute('data-votes') || '0', 10);
        if (votes === maxVotes) {
            item.classList.add('is-winner');
            if (!item.querySelector('.choice-winner-tag')) {
                const content = item.querySelector('.choice-content');
                if (content) {
                    const tag = document.createElement('span');
                    tag.className = 'choice-winner-tag';
                    tag.innerHTML = `
                        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                            <path d="M6 9H4.5a2.5 2.5 0 0 1 0-5H6"></path>
                            <path d="M18 9h1.5a2.5 2.5 0 0 0 0-5H18"></path>
                            <path d="M4 22h16"></path>
                            <path d="M10 14.66V17c0 .55-.45 1-1 1H7v2h10v-2h-2c-.55 0-1-.45-1-1v-2.34"></path>
                            <path d="M18 2H6v7a6 6 0 0 0 12 0V2z"></path>
                        </svg>
                        Kazanan
                    `;
                    const selectedTag = content.querySelector('.choice-selected-tag');
                    if (selectedTag) {
                        content.insertBefore(tag, selectedTag);
                    } else {
                        content.appendChild(tag);
                    }
                }
            }
        }
    });
}

function initBookmarks() {
    document.addEventListener('click', async (e) => {
        const bookmarkBtn = e.target.closest('.btn-bookmark');
        if (!bookmarkBtn) return;

        const pollId = bookmarkBtn.dataset.pollId;
        if (!pollId) return;

        bookmarkBtn.disabled = true;
        try {
            const csrfToken = getCookie('csrftoken');
            const res = await fetch(`/api/poll/${pollId}/bookmark/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken || '',
                }
            });
            const data = await res.json();
            if (data.success) {
                const icon = bookmarkBtn.querySelector('svg');
                if (data.bookmarked) {
                    bookmarkBtn.classList.add('active');
                    bookmarkBtn.title = 'Kaydedilenlerden Çıkar';
                    if (icon) icon.setAttribute('fill', 'currentColor');
                } else {
                    bookmarkBtn.classList.remove('active');
                    bookmarkBtn.title = 'Kaydet';
                    if (icon) icon.setAttribute('fill', 'none');

                    const card = bookmarkBtn.closest('.poll-card[data-category="bookmarked"]');
                    if (card) {
                        card.style.opacity = '0.35';
                    }
                }
                showToast(data.message);
            } else {
                showToast(data.error || 'İşlem gerçekleştirilemedi.');
            }
        } catch (err) {
            console.error(err);
            showToast('Bağlantı hatası oluştu.');
        } finally {
            bookmarkBtn.disabled = false;
        }
    });
}
