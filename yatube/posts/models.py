from django.db import models
from django.contrib.auth import get_user_model
from django.db.models import CheckConstraint, F, Q
from django.urls import reverse

from core.models import CreatedModel

User = get_user_model()


class Group(models.Model):
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=100, unique=True)
    description = models.TextField()

    def __str__(self) -> str:
        return self.title

    def get_absolute_url(self):
        return reverse('posts:group_list', kwargs={'slug': self.slug})


class Post(CreatedModel):
    text = models.TextField('Текст поста',
                            help_text='Введите текст поста')
    pub_date = models.DateTimeField('Дата публикации',
                                    auto_now_add=True)
    author = models.ForeignKey(User,
                               on_delete=models.CASCADE,
                               verbose_name='Автор')
    group = models.ForeignKey(Group,
                              blank=True,
                              null=True,
                              on_delete=models.SET_NULL,
                              verbose_name='Группа',
                              help_text='Выберите группу')
    image = models.ImageField('Картинка',
                              upload_to='posts/',
                              blank=True)

    def __str__(self) -> str:
        return self.text[0:15]

    class Meta:
        ordering = ['-pub_date']
        default_related_name = 'posts'
        verbose_name = 'Пост'
        verbose_name_plural = 'Посты'

    def get_absolute_url(self):
        return reverse('posts:post_detail', kwargs={'post_id': self.pk})


class Comment(models.Model):
    post = models.ForeignKey(
        to='Post',
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name='Запись'
    )
    author = models.ForeignKey(
        to=User,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name='Автор'
    )
    text = models.TextField(
        max_length=500,
        verbose_name='Текст',
        help_text='Напишите комментарий'
    )
    created = models.DateTimeField(
        verbose_name='Дата публикации',
        auto_now_add=True
    )

    class Meta:
        verbose_name = 'Комментарий'
        verbose_name_plural = 'Комментарии'

    def __str__(self):
        return self.text[:15]


class Follow(models.Model):
    user = models.ForeignKey(
        to=User,
        on_delete=models.CASCADE,
        related_name='follower',
        verbose_name='Подписчик',
    )
    author = models.ForeignKey(
        to=User,
        on_delete=models.CASCADE,
        related_name='following',
        verbose_name='Подписан на',
    )

    class Meta:
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'
        constraints = [
            CheckConstraint(check=~Q(user=F('author')), name='user!=author')
        ]

    def __str__(self):
        return f'{self.user} подписан на {self.author}'
