from django.test import TestCase, Client
from django.urls import reverse
from django.core.cache import cache
from users.models import CustomUser
from polls.models import Poll, Choice


class PollSecurityTests(TestCase):
    def setUp(self):
        cache.clear()
        self.client = Client()
        self.author = CustomUser.objects.create_user(
            username='author',
            email='author@example.com',
            password='StrongPassword123!'
        )
        self.other_user = CustomUser.objects.create_user(
            username='otheruser',
            email='other@example.com',
            password='StrongPassword123!'
        )
        self.poll = Poll.objects.create(
            author=self.author,
            question="Deneme Soru?"
        )
        self.choice1 = Choice.objects.create(poll=self.poll, text="Seçenek A", order=0)
        self.choice2 = Choice.objects.create(poll=self.poll, text="Seçenek B", order=1)

    def test_open_redirect_mitigation_on_toggle_active(self):
        """Ensure malicious next URL is not followed in toggle active."""
        self.client.login(username='author', password='StrongPassword123!')
        response = self.client.post(
            reverse('polls:poll_toggle_active', args=[self.poll.id]),
            {'next': 'https://evil-phishing-site.com'}
        )
        self.assertEqual(response.status_code, 302)
        # Should redirect to poll detail, not evil site
        self.assertEqual(response.url, reverse('polls:poll_detail', args=[self.poll.id]))

    def test_idor_protection_on_toggle_active(self):
        """Ensure other users cannot toggle active status of poll."""
        self.client.login(username='otheruser', password='StrongPassword123!')
        response = self.client.post(
            reverse('polls:poll_toggle_active', args=[self.poll.id])
        )
        self.assertEqual(response.status_code, 403)

    def test_idor_protection_on_delete(self):
        """Ensure other users cannot delete poll."""
        self.client.login(username='otheruser', password='StrongPassword123!')
        response = self.client.post(
            reverse('polls:poll_delete', args=[self.poll.id])
        )
        self.assertEqual(response.status_code, 403)
        self.assertTrue(Poll.objects.filter(id=self.poll.id).exists())

    def test_choice_max_length_validation_server_side(self):
        """Ensure choices with text > 200 chars are rejected without crashing."""
        self.client.login(username='author', password='StrongPassword123!')
        too_long_choice = 'A' * 201
        response = self.client.post(
            reverse('polls:poll_create'),
            {
                'question': 'Yeni Soru?',
                'choices': ['Normal Seçenek', too_long_choice],
                'duration': 24
            }
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "en fazla 200 karakter olabilir")

    def test_vote_flood_rate_limiting(self):
        """Ensure rapid automated vote flooding receives 429 status."""
        cache.clear()
        # First vote should pass
        res1 = self.client.post(
            reverse('polls:vote_api', args=[self.poll.id]),
            {'choice_id': self.choice1.id}
        )
        self.assertEqual(res1.status_code, 200)

        # Immediate second vote should be rate-limited
        res2 = self.client.post(
            reverse('polls:vote_api', args=[self.poll.id]),
            {'choice_id': self.choice2.id}
        )
        self.assertEqual(res2.status_code, 429)

