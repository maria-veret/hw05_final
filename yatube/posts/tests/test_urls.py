from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from django.urls import reverse
from django.core.cache import cache

from posts.models import Post, Group

User = get_user_model()


class PostURLTests(TestCase):
    """Тестируем urls."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовый заголовок',
            slug='test-slug',
            description='Тестовое описание'
        )
        cls.post = Post.objects.create(
            text='Тестовый текст',
            author=cls.user,
            group=cls.group,
        )

    def setUp(self):
        self.guest_client = Client()
        self.user = User.objects.create_user(username='HasNoName')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.author_client = Client()
        self.author_client.force_login(PostURLTests.user)
        cache.clear()

    def test_url_exists_at_desired_location(self):
        """Проверка страниц, доступных любому пользователю."""
        reverse_names = [
            reverse('posts:index'),
            reverse('posts:group_list', kwargs={'slug': self.group.slug}),
            reverse('posts:profile', kwargs={'username': self.user.username}),
            reverse('posts:post_detail', kwargs={'post_id': self.post.id})
        ]
        for reverse_name in reverse_names:
            with self.subTest(reverse_name=reverse_name):
                response = self.guest_client.get(reverse_name)
                self.assertEqual(response.status_code, 200)

    def test_url_for_auth_user(self):
        """Проверка страницы создания поста, доступной
        авторизированному пользователю."""
        response = self.authorized_client.get(reverse('posts:post_create'))
        self.assertEqual(response.status_code, 200)

    def test_url_for_author(self):
        """Проверка страницы изменения поста, доступной
        автору поста."""
        response = self.author_client.get(reverse(
            'posts:post_edit', kwargs={'post_id': self.post.id}))
        self.assertEqual(response.status_code, 200)

    def test_page_for_404(self):
        """Проверка недоступности страницы с несуществующим адресом."""
        response = self.guest_client.get('/unexisting_page/')
        self.assertEqual(response.status_code, 404)

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_reverse_names = {
            'posts/index.html': reverse('posts:index'),
            'posts/group_list.html': reverse(
                'posts:group_list',
                kwargs={'slug': self.group.slug}
            ),
            'posts/profile.html': reverse(
                'posts:profile',
                kwargs={'username': self.user.username}
            ),
            'posts/post_detail.html': reverse(
                'posts:post_detail',
                kwargs={'post_id': self.post.id}
            ),
            'posts/create_post.html': reverse('posts:post_create'),
            'posts/update_post.html': reverse(
                'posts:post_edit',
                kwargs={'post_id': self.post.id}
            ),
        }
        for template, reverse_names in templates_reverse_names.items():
            with self.subTest(reverse_names=reverse_names):
                response = self.author_client.get(reverse_names)
                self.assertTemplateUsed(response, template)
