from django.test import TestCase, Client
from django.urls import reverse
from django import forms
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile

from ..models import Post, Group, User, Follow


class PostsVIEWTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(username='test_user')
        cls.group = Group.objects.create(
            title='Test title',
            slug='test_slug',
            description='Test description',
        )
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
        cls.post = Post.objects.create(
            text='Test text',
            author=cls.user,
            group=cls.group,
            image=uploaded,
        )
        cls.follow = Follow.objects.create(
            user=cls.user,
            author=cls.post.author
        )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        cache.clear()

    def test_correct_templates(self):
        reverse_map = {
            reverse('posts:index'): 'posts/index.html',
            reverse(
                'posts:group_list', kwargs={'slug': 'test_slug'}
            ): 'posts/group_list.html',
            reverse(
                'posts:profile', kwargs={'username': 'test_user'}
            ): 'posts/profile.html',
            reverse(
                'posts:post_detail', kwargs={'post_id': self.post.id}
            ): 'posts/post_detail.html',
            reverse(
                'posts:post_edit', kwargs={'post_id': self.post.id}
            ): 'posts/create_post.html',
            reverse('posts:post_create'): 'posts/create_post.html',
            reverse('posts:follow_index'): 'posts/follow.html'
        }
        for reverse_name, template in reverse_map.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def check_first_page_context(self, first_object: Post):
        self.assertEqual(first_object.text, self.post.text)
        self.assertEqual(first_object.author, self.post.author)
        self.assertEqual(first_object.group, self.post.group)
        self.assertEqual(first_object.image, self.post.image)

    def test_index_context(self):
        response = self.authorized_client.get(reverse('posts:index'))
        contexts = ('title', 'page_obj')
        for context in contexts:
            self.assertIn(context, response.context)
        self.check_first_page_context(response.context['page_obj'][0])

    def test_group_posts_context(self):
        response = self.authorized_client.get(
            reverse('posts:group_list', kwargs={'slug': self.group.slug})
        )
        self.assertIn('group', response.context)
        self.assertIn('page_obj', response.context)
        self.assertEqual(response.context['group'], self.group)
        self.check_first_page_context(response.context['page_obj'][0])

    def test_profile_context(self):
        response = self.authorized_client.get(
            reverse('posts:profile', kwargs={'username': self.user})
        )
        contexts = ('author', 'page_obj')
        for context in contexts:
            self.assertIn(context, response.context)
        self.assertEqual(response.context['author'], self.user)
        self.check_first_page_context(response.context['page_obj'][0])

    def test_post_detail_context(self):
        response = self.authorized_client.get(
            reverse('posts:post_detail', kwargs={'post_id': self.post.id})
        )
        contexts = ('post', 'comment_form', 'comments')
        for context in contexts:
            self.assertIn(context, response.context)
        self.assertEqual(response.context['post'], self.post)
        self.check_first_page_context(response.context['post'])

    def test_post_create_context(self):
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
            'image': forms.fields.ImageField,
        }
        response = self.authorized_client.get(reverse('posts:post_create'))
        for field, form in form_fields.items():
            with self.subTest(field=field):
                result = response.context.get('form').fields.get(field)
                self.assertIsInstance(result, form)

    def test_post_edit_context(self):
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
            'image': forms.fields.ImageField,
        }
        response = self.authorized_client.get(
            reverse('posts:post_edit', kwargs={'post_id': self.post.id})
        )
        for field, form in form_fields.items():
            with self.subTest(value=field):
                result = response.context.get('form').fields.get(field)
                self.assertIsInstance(result, form)

    def test_add_comment_context(self):
        response = self.authorized_client.get(
            reverse('posts:add_comment', kwargs={'post_id': self.post.id})
        )
        self.assertRedirects(
            response, reverse(
                'posts:post_detail', kwargs={'post_id': self.post.id}
            )
        )

    def test_follow_index_context(self):
        response = self.authorized_client.get(reverse('posts:follow_index'))
        self.assertIn('title', response.context)
        self.assertIn('page_obj', response.context)
        self.check_first_page_context(response.context['page_obj'][0])

    def test_profile_follow(self):
        self.authorized_client.get(
            reverse('posts:profile_follow', kwargs={'username': self.user})
        )
        response = self.authorized_client.get(reverse('posts:follow_index'))
        self.assertEqual(response.context['page_obj'][0], self.post)

    def test_profile_unfollow(self):
        self.authorized_client.get(
            reverse('posts:profile_unfollow', kwargs={'username': self.user})
        )
        response = self.authorized_client.get(reverse('posts:follow_index'))
        self.assertEqual(response.context.get('post'), None)


class PostsPAGINATORTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(username='test_user')
        cls.group = Group.objects.create(
            title='Test title',
            slug='test_slug',
            description='Test description',
        )
        for post in range(11):
            cls.post = Post.objects.create(
                text='Test text',
                author=cls.user,
                group=cls.group,
            )
        cls.pages = (
            reverse('posts:index'),
            reverse('posts:group_list', kwargs={'slug': cls.group.slug}),
            reverse('posts:profile', kwargs={'username': cls.user})
        )

    def setUp(self):
        self.guest_client = Client()

    def test_get_first_page_objects(self):
        for page in self.pages:
            response = self.guest_client.get(page)
            self.assertEqual(len(response.context['page_obj']), 10)

    def test_get_second_page_objects(self):
        for page in self.pages:
            response = self.guest_client.get(page + '?page=2')
            self.assertEqual(len(response.context['page_obj']), 1)
