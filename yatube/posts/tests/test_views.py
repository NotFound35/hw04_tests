import shutil
import tempfile

from django.core.cache import cache
from django import forms
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.conf import settings
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..models import Comment, Group, Post

User = get_user_model()

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.user2 = User.objects.create_user(username='user2')
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        cls.group1 = Group.objects.create(
            title='title',
            slug='slug',
            description='description'
        )
        cls.group2 = Group.objects.create(
            title='title2',
            slug='slug2',
            description='description2'
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='testtext',
            group=cls.group1,
            image=uploaded
        )
        cls.comment = Comment.objects.create(
            text='Commenttext',
            author=cls.user,
            post=PostViewsTest.post
        )

    @classmethod
    def tearDownClass(cls):
        super(). tearDownClass
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.guest_client = Client()
        self.auth_client = Client()
        self.auth_client.force_login(self.user)

    def page_obj_in_context(self, context, post=False):
        """Универсальный модуль"""
        if post:
            self.assertIn('post', context)
            first_obj = context['post']
        else:
            self.assertIn('page_obj', context)
            first_obj = context['page_obj'][0]
        self.assertEqual(first_obj.author.username, 'auth')
        self.assertEqual(first_obj.text, 'testtext')
        self.assertEqual(first_obj.group.title, 'title')
        self.assertEqual(first_obj.image, PostViewsTest.post.image)

    def test_correct_template_name(self):
        """Проверка name"""
        template_name_pages = {
            reverse('posts:main_page'): 'posts/index.html',
            reverse('posts:group_list', kwargs={'slug': 'slug'}):
                'posts/group_list.html',
            reverse('posts:profile', kwargs={'username': self.user}):
                'posts/profile.html',
            reverse('posts:post_detail', kwargs={'post_id': self.post.id}):
                'posts/post_detail.html',
            reverse('posts:post_create'): 'posts/create_post.html',
            reverse('posts:post_edit', kwargs={'post_id': self.post.id}):
                'posts/create_post.html'
        }
        for name, template in template_name_pages.items():
            with self.subTest(name=name):
                response = self.auth_client.get(name)
                self.assertTemplateUsed(response, template)

    def test_main_page_show_correct_context(self):
        """Проверка контекста на main_page(index)"""
        response = self.auth_client.get(reverse('posts:main_page'))
        self.page_obj_in_context(response.context)

    def test_group_list_show_correct_context(self):
        """Проверка контекста group_list"""
        response = self.auth_client.get(reverse(
            'posts:group_list',
            kwargs={'slug': self.group1.slug}))
        first_obj = response.context.get('group')
        self.assertEqual(first_obj, Group.objects.get(id=1))
        self.page_obj_in_context(response.context)

    def test_profile_show_correct_context(self):
        """Проверка контекста profile"""
        response = self.auth_client.get(reverse(
                                        'posts:profile',
                                        kwargs={'username': self.user.username}
                                        ))
        first_obj = response.context.get('author')
        self.assertEqual(first_obj, self.user)
        self.page_obj_in_context(response.context)

    def test_post_detail_show_correct_context(self):
        """Проверка контекста post_detail"""
        response = self.auth_client.get(reverse(
                                        'posts:post_detail',
                                        kwargs={'post_id': self.post.id}))
        post_obj = response.context.get('post')
        post_count = response.context.get('post_count')
        comments_count = response.context.get('comments_count')
        expected_comments_count = Comment.objects.filter(
            post_id=self.post.id).count()
        expected_count = Post.objects.filter(author=post_obj.author).count()
        self.assertEqual(comments_count, expected_comments_count)
        self.assertEqual(post_obj, self.post)
        self.assertEqual(post_count, expected_count)
        self.page_obj_in_context(response.context, post=True)

    def test_unauth_user_cant_post(self):
        """Проверка неавторизованного пользователя"""
        post_count = Post.objects.count()
        response = self.guest_client.post(
            reverse('posts:post_create'),
            data={'text': 'testtext',
                  'group': self.group1.id},
            follow=True
        )
        self.assertRedirects(response, '/auth/login/?next=/create/')
        self.assertEqual(Post.objects.count(), post_count)

    form_fields = {
        'group': forms.fields.ChoiceField,
        'text': forms.fields.CharField,
        'image': forms.fields.ImageField,
    }

    def test_edit_post_show_correct_context(self):
        """Проверка контекста редактирования поста"""
        response = self.auth_client.get(reverse(
                                        'posts:post_edit',
                                        kwargs={'post_id': self.post.id}))
        self.assertTrue(response.context['is_edit'])
        for value, expected in self.form_fields.items():
            with self.subTest(value=value):
                field = response.context['form'].fields[value]
                self.assertIsInstance(field, expected)

    def test_create_post_show_correct_context(self):
        """Проверка контекста создания поста"""
        response = self.auth_client.get(reverse('posts:post_create'))
        for value, expected in self.form_fields.items():
            with self.subTest(value=value):
                field = response.context['form'].fields[value]
                self.assertIsInstance(field, expected)

    def test_post_created_in_group_profile(self):
        urls = (
            reverse('posts:group_list', kwargs={'slug': self.group2.slug}),
            reverse('posts:profile', kwargs={'username': self.user2.username})
        )
        for url in urls:
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                page_obj = response.context.get('page_obj')
                self.assertEqual(len(page_obj), 0)

    def test_unauth_user_cant_comment(self):
        """Проверка, что неавторизованный не может оставлять коммент"""
        comment_count = Comment.objects.count()
        response = self.guest_client.post(
            reverse('posts:add_comment', kwargs={'post_id': self.post.id}),
            follow=True
        )
        self.assertRedirects(response,
                             '/auth/login/?next=%2Fposts%2F2%2Fcomment%2F')
        self.assertEqual(Comment.objects.count(), comment_count)


class PaginatorTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='title',
            slug='slug',
            description='description'
        )
        posts = [
            Post(
                text=f'text{i}',
                author=cls.user,
                group=cls.group
            ) for i in range(15)
        ]
        Post.objects.bulk_create(posts)

    def setUp(self):
        self.auth_client = Client()
        self.auth_client.force_login(self.user)

    def test_first_main_page_correct(self):
        response = self.auth_client.get(reverse('posts:main_page'))
        self.assertEqual(len(response.context['page_obj']), 10)

    def test_second_main_page_correct(self):
        response = self.auth_client.get(reverse('posts:main_page') + '?page=2')
        self.assertEqual(len(response.context['page_obj']), 6)

    def test_first_group_list_correct(self):
        response = self.auth_client.get(reverse('posts:group_list',
                                                kwargs={'slug': 'slug'}))
        self.assertEqual(len(response.context['page_obj']), 10)

    def test_second_group_list_correct(self):
        response = self.auth_client.get(reverse(
                                        'posts:group_list',
                                        kwargs={'slug': 'slug'}) + '?page=2')
        self.assertEqual(len(response.context['page_obj']), 5)

    def test_first_profile_page_correct(self):
        response = self.auth_client.get(reverse('posts:profile',
                                                kwargs={'username': self.user}
                                                ))
        self.assertEqual(len(response.context['page_obj']), 10)

    def test_second_profile_page_correct(self):
        response = self.auth_client.get(reverse(
                                        'posts:profile',
                                        kwargs={'username': self.user}
                                        ) + '?page=2')
        self.assertEqual(len(response.context['page_obj']), 5)


class TestCache(TestCase):
    """Проверка кэша"""
    def test_cache(self):
        response = self.client.get(reverse('posts:main_page'))
        self.assertEqual(len(response.context['page_obj']), 0)
        user = User.objects.create_user(username='auth')
        Post.objects.create(
            text='TestText',
            author=user
        )
        self.assertEqual(len(response.context['page_obj']), 0)
        cache.clear()
        self.assertEqual(len(response.context['page_obj']), 0)
