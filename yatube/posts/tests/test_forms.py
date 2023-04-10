import shutil
import tempfile
from io import BytesIO

from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image
from django.conf import settings

from posts.models import Comment, Group, Post, get_user_model


User = get_user_model()

POST_CREATE = reverse('posts:post_create')

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostFormTests(TestCase):
    @staticmethod
    def get_image_for_test(name: str) -> SimpleUploadedFile:
        with BytesIO() as output:
            Image.new('RGB', (1280, 1024), color=1).save(output, 'BMP')
            data = output.getvalue()
        image = SimpleUploadedFile(
            name=name,
            content=data,
            content_type='image'
        )
        return image

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create(username='Ekaterina')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Описание'
        )
        cls.post = Post.objects.create(
            author=cls.author,
            text='Тестовый пост',
            group=cls.group
        )
        cls.new_group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug_1',
            description='Описание'
        )
        cls.post_edit = reverse('posts:post_edit',
                                args=[PostFormTests.post.id])
        cls.second_group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug_2',
            description='Описание'
        )
        cls.test_user = User.objects.create(
            username='test_user'
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.author)
        self.auth_user = Client()
        self.auth_user.force_login(self.test_user)

    def test_post_form_create_new_post(self):
        """Новая запись с картинкой сохраняется в БД."""
        self.form_data = {'text': 'Другой текст',
                          'group': self.new_group.id, }
        posts_count = Post.objects.count()
        image = self.get_image_for_test('post.bmp')
        form_data = {
            'text': 'text_post_2',
            'group': self.new_group.id,
            'image': image
        }
        ids = list(Post.objects.all().values_list('id', flat=True))
        response = self.authorized_client.post(
            POST_CREATE,
            data=self.form_data,
            follow=True
        )
        self.assertEqual(Post.objects.count(), posts_count + 1)
        posts = Post.objects.exclude(id__in=ids)
        self.assertEqual(posts.count(), 1)
        post = posts[0]
        self.assertEqual(self.form_data['text'], post.text,
                         'Текст не совпадает!')
        self.assertEqual(self.form_data['group'], post.group.id)
        self.assertRedirects(response, reverse('posts:profile',
                             kwargs={'username': post.author}))
        self.assertTrue(Post.objects.filter(
            text=form_data['text'],
            group=self.new_group,
            author=self.test_user,
            image='posts/post.bmp'
        ).exists())

    def test_edit_post_in_form(self):
        """Отредактированная запись сохраняется в БД."""
        self.form_data = {'text': 'Другой текст',
                          'group': self.second_group.id, }
        response = self.authorized_client.post(self.post_edit,
                                               data=self.form_data,
                                               follow=True)
        self.post.refresh_from_db()
        self.assertEqual(self.post.text, self.form_data['text'])
        self.assertEqual(self.post.group.id, self.form_data['group'])
        self.assertRedirects(response, reverse('posts:post_detail',
                                               args=[PostFormTests.post.id]))

    def test_add_comment(self):
        """
        После успешного добавления комментарий
        появляется на странице записи.
        """
        page = reverse('posts:post_detail', kwargs={'post_id': self.post.id})
        comments_count = Comment.objects.filter(post=self.post.id).count()
        comment_form_data = {'text': 'new_test_comment', }
        response = self.auth_user.post(
            reverse('posts:add_comment', kwargs={'post_id': self.post.id}),
            data=comment_form_data,
            follow=True
        )
        self.assertRedirects(response, page)
        self.assertEqual(Comment.objects.filter(post=self.post.id).count(),
                         comments_count + 1)
        response = self.auth_user.get(page)
        comment_on_page = response.context.get('comments')[0]
        self.assertEqual(comment_on_page.author, self.test_user)
        self.assertEqual(comment_on_page.post, self.post)
        self.assertEqual(comment_on_page.text, comment_form_data['text'])
