from django.test import TestCase
from django.urls import reverse

from posts.models import Group, Post, Comment, Follow, get_user_model

User = get_user_model()


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.following_user = User.objects.create_user(
            username='following_user'
        )
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
        )
        cls.follow = Follow.objects.create(
            user=cls.user,
            author=cls.following_user
        )
        cls.comment = Comment.objects.create(
            post=cls.post,
            author=cls.user,
            text='comment',
        )
        cls.post_detail = reverse('posts:post_detail',
                                  kwargs={'post_id': cls.post.id})
        cls.group_list = reverse('posts:group_list',
                                 kwargs={'slug': cls.group.slug})

    def test_models_have_correct_object_names(self):
        """Проверяем, что у моделей корректно работает __str__."""
        expected_models_str_value = {
            self.post: self.post.text[:15],
            self.group: self.group.title,
            self.follow: f'{self.user} подписан на {self.following_user}',
            self.comment: self.comment.text[:15]
        }
        for model_obj, expected_str_value in expected_models_str_value.items():
            with self.subTest(model_object=model_obj):
                self.assertEqual(expected_str_value, str(model_obj))

    def test_post_field_verbose_name(self):
        """verbose_name полей модели Post совпадает с ожидаемым значением."""
        field_verbose_name = {
            'text': 'Текст поста',
            'group': 'Группа',
            'author': 'Автор',
        }
        for field, expected_verbose_name in field_verbose_name.items():
            with self.subTest(field=field):
                self.assertEqual(
                    self.post._meta.get_field(field).verbose_name,
                    expected_verbose_name)

    def test_post_field_help_text(self):
        """help_text полей модели Post совпадает с ожидаемым."""
        field_help_text = {
            'text': 'Введите текст поста',
            'group': 'Выберите группу',
        }
        for field, expected_help_text in field_help_text.items():
            with self.subTest(field=field):
                self.assertEqual(
                    self.post._meta.get_field(field).help_text,
                    expected_help_text)

    def test_get_absolute_url(self):
        """Метод get_absolute_url в моделях Group и Post возвращает ссылку
        на страницу группы и детали записи соответственно.
        """
        expected_urls_by_method = {
            self.post: self.post_detail,
            self.group: self.group_list,
        }
        for model, expected_url in expected_urls_by_method.items():
            self.assertEqual(model.get_absolute_url(), expected_url)
