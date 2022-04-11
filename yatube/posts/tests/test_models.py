from django.contrib.auth import get_user_model
from django.test import TestCase

from posts.models import Post, Group, User, Comment

User = get_user_model()


class YatubeModelTest(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='Тестовый слаг',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
            group=cls.group,
        )
        cls.comment = Comment.objects.create(
            text='Комментарий',
            author=cls.user,
            post=cls.post,
        )

    def test_models_have_correct_object_names(self):
        """Проверяем, что у модели корректно работает __str__."""
        group = self.group
        expected_object_name = group.title
        self.assertEqual(expected_object_name, str(group))

    def test_models_have_correct_object_names(self):
        """Проверяем, что у модели корректно работает __str__."""
        post = self.post
        expected_object_name = post.text[:15]
        self.assertEqual(expected_object_name, str(post))

    def test_models_have_correct_object_names(self):
        """Проверяем, что у модели корректно работает __str__."""
        comment = self.comment
        expected_object_name = comment.text[:15]
        self.assertEqual(expected_object_name, str(comment))
