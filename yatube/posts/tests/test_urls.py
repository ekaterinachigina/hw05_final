from http import HTTPStatus

from django.test import TestCase, Client
from django.urls import reverse
from django.core.cache import cache

from posts.models import Group, Post, get_user_model


User = get_user_model()

MAIN_PAGE = reverse('posts:index')

POST_CREATE = reverse('posts:post_create')


class StaticURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.guest_client = Client()
        cls.user = User.objects.create_user(username='HasNoName')
        cls.author = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='test-group',
            slug='test-slug',
            description='test-description',
        )
        cls.post = Post.objects.create(
            author=cls.author,
            text='test-text',
            group=cls.group,
        )
        cls.group_list = reverse('posts:group_list',
                                 kwargs={'slug': cls.group.slug})
        cls.profile = reverse('posts:profile',
                              kwargs={'username': cls.user.username})
        cls.post_detail = reverse('posts:post_detail',
                                  kwargs={'post_id': cls.post.id})
        cls.post_edit = reverse('posts:post_edit',
                                kwargs={'post_id': cls.post.id})

    def setUp(self):
        self.user = User.objects.create_user(username='StasBasov')
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.author_client = Client()
        self.author_client.force_login(self.author)
        cache.clear()

    def test_url_for_author_user(self):
        templates_url_names = {
            MAIN_PAGE: 'posts/index.html',
            POST_CREATE: 'posts/post_create.html',
            self.group_list: 'posts/group_list.html',
            self.profile: 'posts/profile.html',
            self.post_detail: 'posts/post_detail.html',
            self.post_edit: 'posts/post_create.html',
        }
        for reverse_name in templates_url_names.keys():
            with self.subTest(reverse_name=reverse_name):
                response = self.author_client.get(reverse_name)
                self.assertEqual(response.status_code, HTTPStatus.OK)

        """ Тестовый URL для авторизированного пользователя """
        for reverse_name in templates_url_names.keys():
            with self.subTest(reverse_name=reverse_name):
                if reverse_name == self.post_edit:
                    response = self.authorized_client.get(reverse_name)
                    self.assertEqual(response.status_code, HTTPStatus.FOUND)
                else:
                    response = self.authorized_client.get(reverse_name)
                    self.assertEqual(response.status_code, HTTPStatus.OK)

        """ Тестовый URL для гостевого пользователя """
        for reverse_name in templates_url_names.keys():
            with self.subTest(reverse_name=reverse_name):
                if reverse_name == POST_CREATE:
                    response = self.guest_client.get(reverse_name)
                    print(response)
                    self.assertEqual(response.status_code, HTTPStatus.FOUND)
                elif reverse_name == self.post_edit:
                    response = self.guest_client.get(reverse_name)
                    self.assertEqual(response.status_code, HTTPStatus.FOUND)
                else:
                    response = self.guest_client.get(reverse_name)
                    self.assertEqual(response.status_code, HTTPStatus.OK)

        """ В тестовых URL используется корректный шаблон """
        for address, template in templates_url_names.items():
            with self.subTest(address=address):
                response = self.author_client.get(address)
                self.assertTemplateUsed(response, template)
