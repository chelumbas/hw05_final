from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, Client
from django.urls import reverse


from ..forms import PostForm
from ..models import Post, User


class PostsFORMSTest(TestCase):
    image = (
        b'\x47\x49\x46\x38\x39\x61\x02\x00\x01\x00\x80'
        b'\x00\x00\x00\x00\x00\xFF\xFF\xFF\x21\xF9\x04'
        b'\x00\x00\x00\x00\x00\x2C\x00\x00\x00\x00\x02'
        b'\x00\x01\x00\x00\x02\x02\x0C\x0A\x00\x3B'
    )

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(username='test_user')
        cls.post = Post.objects.create(
            text='Test text',
            author=cls.user,
        )
        cls.form = PostForm()

    def setUp(self) -> None:
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_success_create_post(self):
        new_file = self.image
        uploaded = SimpleUploadedFile(
            name='new_file.png',
            content=new_file,
            content_type='image/png'
        )
        posts_count = Post.objects.count()
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data={'text': 'Test new post', 'image': uploaded},
            follow=True
        )
        self.assertEqual(Post.objects.count(), posts_count + 1)
        self.assertRedirects(
            response, reverse('posts:profile', kwargs={'username': self.user})
        )

    def test_success_edit_post(self):
        new_file = self.image
        uploaded = SimpleUploadedFile(
            name='new_file.png',
            content=new_file,
            content_type='image/png'
        )
        response = self.authorized_client.post(
            reverse('posts:post_edit', kwargs={'post_id': self.post.id}),
            data={'text': 'Test new text', 'image': uploaded},
            follow=True,
        )
        self.assertRedirects(
            response,
            reverse('posts:post_detail', kwargs={'post_id': self.post.pk})
        )
