from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import Client, TestCase

from ..models import Group, Post

User = get_user_model()


class StaticURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.author = User.objects.create_user(username='testuser')
        cls.post = Post.objects.create(
            text='тестовый текст',
            author=cls.user,
        )
        cls.group = Group.objects.create(
            title='title',
            slug='slug',
            description='descripton',
        )

    def setUp(self):
        self.guest_client = Client()
        self.auth_client = Client()
        self.auth_client.force_login(self.user)
        self.authorized_user = Client()
        self.authorized_user.force_login(self.author)

    def test_all_url(self):
        """Проверка страниц общего доступа"""
        template_status = {
            '/': HTTPStatus.OK,
            '/group/slug/': HTTPStatus.OK,
            '/profile/auth/': HTTPStatus.OK,
            f'/posts/{StaticURLTests.post.id}/': HTTPStatus.OK
        }
        for url, status in template_status.items():
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                self.assertEqual(response.status_code, status)

    def test_posts_post_id_edit_url(self):
        """Редактирование поста для автора"""
        response = self.authorized_user.get(
            f'/posts/{StaticURLTests.post.id}/edit/')
        self.assertRedirects(response, (
            f'/posts/{StaticURLTests.post.id}/'))

    def test_posts_create_url(self):
        """Проверка создания дла зарегистрированного пользователя"""
        response = self.auth_client.get('/create/')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_posts_create_none_auth_url(self):
        """Проверка создания для незарегистрированного пользователя"""
        response = self.guest_client.get('/create/')
        self.assertRedirects(response, '/auth/login/?next=/create/')

    def test_404_page(self):
        """Тест несуществующей страницы"""
        response = self.guest_client.get('404')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_urls_uses_correct(self):
        """Проверка шаблонов"""
        templates_url_names = {
            '/': 'posts/index.html',
            '/group/slug/': 'posts/group_list.html',
            '/profile/auth/': 'posts/profile.html',
            f'/posts/{StaticURLTests.post.id}/': 'posts/post_detail.html',
            f'/posts/{StaticURLTests.post.id}/edit/': 'posts/create_post.html',
            '/create/': 'posts/create_post.html',
        }
        for url, template in templates_url_names.items():
            with self.subTest(address=url):
                response = self.auth_client.get(url)
                self.assertTemplateUsed(response, template)
