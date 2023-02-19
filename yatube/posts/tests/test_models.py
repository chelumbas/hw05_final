from django.contrib.auth import get_user_model
from django.test import TestCase

from ..models import Group, Post, Comment

User = get_user_model()


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='test_user')
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый текст для тестов',
        )
        cls.group = Group.objects.create(
            title='Test title',
            slug='Test slug',
            description='Test description',
        )
        cls.comment = Comment.objects.create(
            text='Test comment',
            post=cls.post,
            author=cls.user
        )

    def test_post_verbose_name(self):
        verbose_names = {
            'text': 'Текст поста',
            'group': 'Группа',
            'image': 'Картинка'
        }
        for verbose_name, expected_name in verbose_names.items():
            with self.subTest(verbose_name=verbose_name):
                self.assertEqual(
                    self.post._meta.get_field(verbose_name).verbose_name,
                    expected_name
                )

    def test_post_help_text(self):
        help_texts = {
            'text': 'Текст нового поста',
            'group': 'Группа, к которой будет относиться пост',
            'image': 'Картинка для твоего поста поста <3'
        }
        for help_text, expected_text in help_texts.items():
            with self.subTest(help_text=help_text):
                self.assertEqual(
                    self.post._meta.get_field(help_text).help_text,
                    expected_text
                )

    def test_post_object_names(self):
        post = self.post
        self.assertEqual(str(post), post.text[:15])

    def test_group_verbose_name(self):
        verbose_names = {
            'title': 'Название',
            'slug': 'Ключ',
            'description': 'Описание'
        }
        for verbose_name, expected_name in verbose_names.items():
            with self.subTest(verbose_name=verbose_name):
                self.assertEqual(
                    self.group._meta.get_field(verbose_name).verbose_name,
                    expected_name
                )

    def test_group_help_text(self):
        help_texts = {
            'title': 'Название группы',
            'slug': 'Короткое имя группы',
            'description': 'Опиши деятельность группы'
        }
        for help_text, expected_text in help_texts.items():
            with self.subTest(help_text=help_text):
                self.assertEqual(
                    self.group._meta.get_field(help_text).help_text,
                    expected_text
                )

    def test_group_object_names(self):
        group = self.group
        self.assertEqual(str(group), group.title)

    def test_comment_verbose_name(self):
        self.assertEqual(
            self.comment._meta.get_field('text').verbose_name, 'Текст'
        )
        self.assertEqual(
            self.comment._meta.get_field('text').help_text, 'Текст комментария'
        )

    def test_comment_object_names(self):
        comment = self.comment
        self.assertEqual(str(comment), comment.text)
