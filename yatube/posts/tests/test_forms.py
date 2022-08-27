from unittest import TestCase
from ..forms import PostForm
from ..models import Post, Group
from django.urls import reverse
from django.test import TestCase, Client
from django.contrib.auth import get_user_model

User = get_user_model()


class PostCreateFormTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.form = PostForm()
        cls.user = User.objects.create_user(username='auth')
        cls.post = Post.objects.create(
            text='test-text',
            author=cls.user
        )
        cls.group = Group.objects.create(
            title='title',
            slug='slug',
            description='description'
        )

    def setUp(self):
        self.auth_user = Client()
        self.auth_user.force_login(self.user)

    def test_create_post_form(self):
        post_count = Post.objects.count()
        form_data = {
            'text': 'text',
            'group': self.group.id
        }
        response = self.auth_user.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )

        self.assertEqual(response.status_code, 200)
        self.assertRedirects(response, reverse('posts:profile',
                                               kwargs={'username': self.user}))
        self.assertEqual(Post.objects.count(), post_count + 1)
        self.assertTrue(Post.objects.filter(
            author=self.user,
            text=form_data['text'],
            id=2).exists())

    def test_edit_post_form(self):
        post_count = Post.objects.count()
        form_data = {
            'text': 'test-text',
            'group': self.group.id
        }

        response = self.auth_user.post(
            reverse('posts:post_edit', args=[self.post.id]),
            data=form_data,
            follow=True
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Post.objects.count(), post_count)
        self.assertEqual(self.post.text, form_data['text'])
