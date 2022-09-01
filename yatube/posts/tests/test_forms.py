from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from ..forms import CommentForm, PostForm
from ..models import Comment, Group, Post

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

        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertRedirects(response, reverse('posts:profile',
                                               kwargs={'username': self.user}))
        self.assertEqual(Post.objects.count(), post_count + 1)
        self.assertTrue(Post.objects.filter(
            author=self.user,
            text=form_data['text'],
            id=3).exists())

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
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(Post.objects.count(), post_count)
        self.assertEqual(self.post.text, form_data['text'])
        self.assertEqual(self.group.id, form_data['group'])


class CommentTest(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.form = CommentForm()
        cls.user = User.objects.create_user(username='auth2')
        cls.post = Post.objects.create(
            text='test-text',
            author=cls.user
        )
        cls.comment = Comment.objects.create(
            text='CommentText',
            author=cls.user,
            post=CommentTest.post
        )

    @classmethod
    def tearDownClass(cls):
        pass

    def setUp(self):
        self.auth_user = Client()
        self.auth_user.force_login(self.user)

    def test_create_comment_form(self):
        comment_count = Comment.objects.count()
        form_data = {
            'text': 'CommentText',
            'author': self.user
        }
        response = self.auth_user.post(
            reverse('posts:add_comment', args=[self.post.id]),
            data=form_data,
            follow=True
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertRedirects(response, reverse(
            'posts:post_detail', kwargs={'post_id': self.post.id}
        ))
        self.assertEqual(Comment.objects.count(), comment_count + 1)
