from django.contrib.auth import get_user_model
from django.test import TestCase

from ..models import Group, Post

User = get_user_model()

class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username = 'auth')
        cls.group = Group.objects.create(
            title = 'Тестовая группа',
            slug = 'Тестовый слаг',
            description = 'Тестовое описание',
        )
        cls.post = Post.objects.create(
            author = cls.user,
            text = 'Тестовый текст'
        )


    def test_model_have_correct_name(self):
        group = PostModelTest.group
        expected_name = group.title
        self.assertEqual(expected_name, str(group))

    def test_model_have_correct(self):
        post = PostModelTest.post
        expected_name = post.text
        self.assertEqual(expected_name, str(post.text[:15]))