import shutil
import tempfile

from django.test import Client, TestCase, override_settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.conf import settings

from posts.forms import Post
from posts.models import Group, User, Comment

User = get_user_model()

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostCreateFormTests(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='Masha')
        cls.group = Group.objects.create(
            title='Тестовый заголовок',
            slug='test-slug',
            description='Тестовое описание'
        )
        cls.post = Post.objects.create(
            text='Тестовый текст',
            author=cls.user,
            group=cls.group
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.guest_user = Client()

    def test_create_post(self):
        """При отправке валидной формы со страницы создания поста
        создается запись в базе данных."""
        posts_count = Post.objects.count()
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
        form_data = {
            'text': 'Текст',
            'group': self.group.id,
            'image': uploaded,
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertRedirects(
            response,
            reverse('posts:profile',
                    kwargs={'username': self.user.username})
        )
        self.assertEqual(Post.objects.count(), posts_count + 1)
        self.assertTrue(
            Post.objects.filter(
                text=form_data['text'],
                group=form_data['group'],
                image='posts/small.gif'
            ).exists()
        )

    def test_post_edit(self):
        """При отправке валидной формы со страницы редактирования
        поста происходит изменение поста."""
        form_data = {
            'text': 'Новый текст',
            'group': self.group.id
        }
        response = self.authorized_client.post(
            reverse('posts:post_edit',
                    kwargs={'post_id': self.post.id}),
            data=form_data,
            follow=True
        )
        self.assertRedirects(response,
                             reverse('posts:post_detail',
                                     kwargs={'post_id': self.post.id}))
        self.assertEqual(
            Post.objects.filter(
                id=self.post.id).last().text, form_data['text']
        )

    def test_authorized_user_create_comment(self):
        """Проверка создания комментария авторизированным пользователем."""
        comments_count = Comment.objects.count()
        form_data = {'text': 'Комментарий'}
        response = self.authorized_client.post(
            reverse('posts:add_comment',
                    kwargs={'post_id': self.post.id}),
            data=form_data,
            follow=True
        )
        self.assertEqual(Comment.objects.count(), comments_count + 1)
        self.assertRedirects(
            response,
            reverse('posts:post_detail', kwargs={'post_id': self.post.id}))
        self.assertTrue(
            Comment.objects.filter(
                text=form_data['text'],
                post_id=self.post.id
            ).exists()
        )

    def test_guest_user_create_comment(self):
        """Проверка создания комментария неавторизированным пользователем."""
        comments_count = Comment.objects.count()
        form_data = {'text': 'Бла бла'}
        response = self.guest_user.post(
            reverse('posts:add_comment',
                    kwargs={'post_id': self.post.id}),
            data=form_data,
            follow=True)
        redirect = reverse('login') + '?next=' + reverse(
            'posts:add_comment', kwargs={'post_id': self.post.id})
        self.assertEqual(Comment.objects.count(), comments_count)
        self.assertRedirects(response, redirect)
