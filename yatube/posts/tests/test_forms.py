import shutil
import tempfile

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, Client, override_settings
from django.urls import reverse
from django.conf import settings

from ..forms import PostForm
from ..models import Post, User, Comment

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostsFORMSTest(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(username='test_user')
        cls.post = Post.objects.create(
            text='Test text',
            author=cls.user,
        )
        cls.form = PostForm()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self) -> None:
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_success_create_post(self):
        posts_count = Post.objects.count()
        image = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00\x01\x00\x80'
            b'\x00\x00\x00\x00\x00\xFF\xFF\xFF\x21\xF9\x04'
            b'\x00\x00\x00\x00\x00\x2C\x00\x00\x00\x00\x02'
            b'\x00\x01\x00\x00\x02\x02\x0C\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='new_file.png',
            content=image,
            content_type='image/png'
        )
        post_fields = {
            'text': 'Test new post',
            'image': uploaded
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=post_fields,
            follow=True
        )
        self.assertRedirects(
            response, reverse('posts:profile', kwargs={'username': self.user})
        )
        self.assertEqual(Post.objects.count(), posts_count + 1)
        self.assertTrue(
            Post.objects.filter(
                text=post_fields['text'],
                image=f'posts/{post_fields["image"]}'
            ).exists()
        )

    def test_success_edit_post(self):
        new_text = 'Test new text'
        posts_count = Post.objects.count()
        response = self.authorized_client.post(
            reverse('posts:post_edit', kwargs={'post_id': self.post.id}),
            data={'text': new_text},
            follow=True,
        )
        self.assertEqual(Post.objects.count(), posts_count)
        self.assertFalse(Post.objects.filter(text=self.post.text).exists())
        self.assertTrue(Post.objects.filter(text=new_text).exists())
        self.assertRedirects(
            response,
            reverse('posts:post_detail', kwargs={'post_id': self.post.pk})
        )

    def test_comment(self):
        comment = 'Test comment'
        comments_count = Comment.objects.count()
        response = self.authorized_client.post(
            reverse('posts:add_comment', kwargs={'post_id': self.post.id}),
            data={'text': comment},
            follow=True,
        )
        self.assertRedirects(
            response,
            reverse('posts:post_detail', kwargs={'post_id': self.post.id})
        )
        self.assertEqual(Comment.objects.count(), comments_count + 1)
        self.assertTrue(
            Comment.objects.filter(text=comment, author=self.user).exists()
        )
