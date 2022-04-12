import tempfile
import shutil

from django.contrib.auth import get_user_model
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django import forms
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.cache import cache

from posts.models import Post, Group, Follow

User = get_user_model()

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostViewsTests(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        cls.uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        cls.user = User.objects.create_user(username='Masha')
        cls.group = Group.objects.create(
            title='Тестовый заголовок',
            slug='test-slug',
            description='Тестовое описание'
        )
        cls.post = Post.objects.create(
            text='Тестовый текст',
            author=cls.user,
            group=cls.group,
            image=cls.uploaded
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.author_client = Client()
        self.author_client.force_login(self.user)
        cache.clear()

    def test_post_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_pages_names = {
            'posts/index.html': reverse('posts:index'),
            'posts/profile.html': (
                reverse('posts:profile',
                        kwargs={'username': self.user.username})),
            'posts/group_list.html': (
                reverse('posts:group_list',
                        kwargs={'slug': self.group.slug})),
            'posts/create_post.html': reverse('posts:post_create'),
            'posts/post_detail.html': (
                reverse('posts:post_detail',
                        kwargs={'post_id': self.post.id})),
            'posts/update_post.html': (
                reverse('posts:post_edit',
                        kwargs={'post_id': self.post.id})),
        }
        for template, reverse_name in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_index_group_list_profile_show_correct_context(self):
        """Шаблоны index group_list profile сформированы
        с правильным контекстом."""
        reverse_names = [
            reverse('posts:index'),
            reverse('posts:group_list', kwargs={'slug': self.group.slug}),
            reverse('posts:profile', kwargs={'username': self.user.username})
        ]
        for reverse_name in reverse_names:
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                first_object = response.context['page_obj'][0]
                author_0 = first_object.author
                text_0 = first_object.text
                group_0 = first_object.group
                post_image_0 = first_object.image
                self.assertEqual(author_0, self.user)
                self.assertEqual(text_0, 'Тестовый текст')
                self.assertEqual(group_0, self.group)
                self.assertEqual(post_image_0, self.post.image)

    def test_post_detail_shows_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse(
            'posts:post_detail', kwargs={'post_id': self.post.id}))
        post_0 = response.context.get('post')
        text_0 = post_0.text
        author_0 = post_0.author
        group_0 = post_0.group
        post_image_0 = post_0.image
        self.assertEqual(author_0, self.user)
        self.assertEqual(text_0, 'Тестовый текст')
        self.assertEqual(group_0, self.group)
        self.assertEqual(post_image_0, self.post.image)

    def test_post_create_show_correct_context(self):
        """Шаблон post_create сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:post_create'))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField
        }
        for fields_name, expected in form_fields.items():
            with self.subTest(value=fields_name):
                form_field = response.context.get(
                    'form').fields.get(fields_name)
                self.assertIsInstance(form_field, expected)

    def test_post_edit_show_correct_context(self):
        """Шаблон post_edit сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse(
            'posts:post_edit', kwargs={'post_id': self.post.id}))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField
        }
        for fields_name, expected in form_fields.items():
            with self.subTest(value=fields_name):
                form_field = response.context.get(
                    'form').fields.get(fields_name)
                self.assertIsInstance(form_field, expected)

    def test_post_appeared_in_index_group_list_profile(self):
        """Пост появляется на страницах сайта."""
        reverse_names = [
            reverse('posts:index'),
            reverse('posts:group_list', kwargs={'slug': self.group.slug}),
            reverse('posts:profile', kwargs={'username': self.user.username})
        ]
        for reverse_name in reverse_names:
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertIn(self.post, response.context['page_obj'])

    def test_post_didnot_appear_on_the_other_groups_page(self):
        """Пост не попал в группу, для которой не был предназначен."""
        response = self.authorized_client.get(reverse(
            'posts:group_list', kwargs={'slug': self.group.slug}))
        self.assertIsNot(self.post, response.context['page_obj'])

    def test_cache(self):
        """Проверка работы кеша."""
        post_1 = Post.objects.create(
            text='Кэш текст',
            author=self.user,
            group=self.group,)
        page_index = self.authorized_client.get(
            reverse('posts:index')).content
        post_1.delete()
        page_delete = self.authorized_client.get(
            reverse('posts:index')).content
        self.assertEqual(page_index, page_delete)
        cache.clear()
        page_cache_clear = self.authorized_client.get(
            reverse('posts:index')).content
        self.assertNotEqual(page_index, page_cache_clear)


class PaginatorViewsTest(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='TestUser')
        cls.group = Group.objects.create(
            title='Тестовый заголовок',
            slug='test-slug',
            description='Тестовое описание'
        )
        for i in range(13):
            Post.objects.create(author=cls.user,
                                group=cls.group,
                                text=f'Пост {i}')

    def setUp(self):
        self.guest_client = Client()
        cache.clear()

    def test_paginator(self):
        """Проверка количества постов на странице."""
        url_pages = [
            reverse('posts:index'),
            reverse('posts:group_list', kwargs={'slug': self.group.slug}),
            reverse('posts:profile', kwargs={'username': self.user.username}),
        ]
        for url in url_pages:
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                self.assertEqual(len(response.context['page_obj']), 10)
                response = self.guest_client.get(url + '?page=2')
                self.assertEqual(len(response.context['page_obj']), 3)


class FollowViewsTest(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author_1 = User.objects.create(username='author_1')
        cls.follower_1 = User.objects.create(username='follower_1')
        cls.post = Post.objects.create(text='Текст для подписки',
                                       author=cls.author_1)

    def setUp(self):
        self.author_client = Client()
        self.author_client.force_login(self.author_1)
        self.follower_client = Client()
        self.follower_client.force_login(self.follower_1)
        cache.clear()

    def test_follow(self):
        """Авторизованный пользователь может подписываться
        на других пользователей."""
        count_follow = Follow.objects.count()
        Follow.objects.create(
            user=self.follower_1,
            author=self.author_1)
        self.follower_client.post(
            reverse('posts:profile_follow',
                    kwargs={'username': self.author_1}))
        self.assertEqual(Follow.objects.count(), count_follow + 1)

    def test_unfollow(self):
        """Авторизованный пользователь может отписываться
        от пользователей."""
        Follow.objects.create(
            user=self.follower_1,
            author=self.author_1)
        count_follow = Follow.objects.count()
        self.follower_client.post(
            reverse('posts:profile_unfollow',
                    kwargs={'username': self.author_1}))
        self.assertEqual(Follow.objects.count(), count_follow - 1)

    def test_followers_lenta(self):
        """Новая запись пользователя появляется в ленте тех,
        кто на него подписан."""
        post = Post.objects.create(
            author=self.author_1,
            text="Текст для подписки")
        Follow.objects.create(
            user=self.follower_1,
            author=self.author_1)
        response = self.follower_client.get(
            reverse('posts:follow_index'))
        self.assertIn(post, response.context['page_obj'])

    def test_notfollowers_lenta(self):
        """Новая запись пользователя не появляется в ленте тех,
        кто на него не подписан."""
        post = Post.objects.create(
            author=self.author_1,
            text="Текст для подписки")
        response = self.follower_client.get(
            reverse('posts:follow_index'))
        self.assertNotIn(post, response.context['page_obj'])
