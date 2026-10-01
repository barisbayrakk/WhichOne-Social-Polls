from django.test import TestCase, Client
from django.urls import reverse
from .models import CustomUser


class UserSecurityTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = CustomUser.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='StrongPassword123!'
        )

    def test_open_redirect_mitigation_on_login(self):
        """Ensure external URLs in next parameter are not followed."""
        response = self.client.post(
            reverse('users:login') + '?next=https://malicious-phishing.com',
            {'username': 'testuser', 'password': 'StrongPassword123!'}
        )
        # Should redirect to default internal feed, not external site
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('polls:feed'))

    def test_safe_internal_redirect_on_login(self):
        """Ensure valid relative URLs in next parameter work properly."""
        response = self.client.post(
            reverse('users:login') + '?next=/create/',
            {'username': 'testuser', 'password': 'StrongPassword123!'}
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, '/create/')

    def test_logout_get_request_rejected(self):
        """Ensure GET request to logout endpoint is rejected (HTTP 405)."""
        self.client.login(username='testuser', password='StrongPassword123!')
        response = self.client.get(reverse('users:logout'))
        self.assertEqual(response.status_code, 405)

    def test_logout_post_request_allowed(self):
        """Ensure POST request to logout endpoint succeeds."""
        self.client.login(username='testuser', password='StrongPassword123!')
        response = self.client.post(reverse('users:logout'))
        self.assertEqual(response.status_code, 302)

