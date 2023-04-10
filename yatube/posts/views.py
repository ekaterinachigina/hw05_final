from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.core.cache import cache
from django.core.exceptions import PermissionDenied
from django.db.models import Q, Count

from .models import Group, Post, User, Follow
from .forms import PostForm, CommentForm
from .utils import get_paginator


def index(request):
    post_list = Post.objects.all().order_by('-pub_date')
    posts_list = cache.get('posts_list')
    if not posts_list:
        posts_list = (Post.objects.select_related('author')
                      .select_related('group').all())
        cache.set('posts_list', posts_list, 20)
    page_obj = get_paginator(request, post_list)
    context = {
        'page_obj': page_obj,
    }
    return render(request, 'posts/index.html', context)


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    post_list = group.posts.all()
    page_obj = get_paginator(request, post_list)
    context = {
        'group': group,
        'page_obj': page_obj,
    }
    return render(request, 'posts/group_list.html', context)


def profile(request, username):
    author = get_object_or_404(User, username=username)
    post_list = author.posts.all()
    page_obj = get_paginator(request, post_list)
    following = (request.user.is_authenticated
                 and Follow.objects.filter(user=request.user,
                                           author=author).exists())
    context = {
        'author': author,
        'page_obj': page_obj,
        'following': following,
    }
    return render(request, 'posts/profile.html', context)


def post_detail(request, post_id):
    post = get_object_or_404(Post.objects.select_related('author')
                             .annotate(count=Count('author__posts')),
                             id=post_id)
    comment_form = CommentForm()
    comments = post.comments.select_related('author').all()
    context = {
        'post': post,
        'comment_form': comment_form,
        'comments': comments,
    }
    return render(request, 'posts/post_detail.html', context)


@login_required
def post_create(request):
    form = PostForm(request.POST or None,
                    files=request.FILES or None)
    context = {
        'form': form,
        'username': request.user,
    }
    if form.is_valid():
        post_create = form.save(commit=False)
        post_create.author = request.user
        post_create.save()
        return redirect('posts:profile', username=post_create.author)
    return render(request, 'posts/post_create.html', context)


@login_required
def post_edit(request, post_id):
    post = Post.objects.get(pk=post_id)
    if request.user.id != post.author.id:
        return redirect('posts:post_detail', post_id=post.id)
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post)
    if form.is_valid():
        form.save()
        return redirect('posts:post_detail', post_id=post_id)
    context = {
        'form': form,
        'is_edit': True,
        'post': post,
        'post_id': post_id,
    }
    return render(request, 'posts/post_create.html', context)


@login_required
def post_delete(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    if request.user != post.author:
        raise PermissionDenied('Удалить запись может только автор')
    post.delete()
    return redirect('posts:profile', post.author.username)


@login_required
def add_comment(request, post_id):
    post = Post.objects.get()
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def follow_index(request):
    follow_posts = cache.get('follow_posts')
    if not follow_posts:
        follow_posts = (
            (Post.objects.select_related('author').select_related('group')
             .filter(author__following__user=request.user)))
        cache.set('follow_posts', follow_posts, 20)
    page_obj = get_paginator(request, follow_posts)
    context = {
        'page_obj': page_obj,
    }
    return render(request, 'posts/follow.html', context)


@login_required
def profile_follow(request, username):
    author = get_object_or_404(User, username=username)
    user = request.user
    if user == author:
        raise PermissionDenied()
    Follow.objects.get_or_create(user=request.user, author=author)
    return render(request, 'posts/follow.html')


@login_required
def profile_unfollow(request, username):
    author = get_object_or_404(User, username=username)
    follow = get_object_or_404(Follow, user=request.user, author=author)
    follow.delete()
    return redirect('posts:index')


def get_search_result(request):
    text = request.GET.get('text')
    if not text:
        return render(request, 'posts/index.html',
                      {'title': 'Введите текст в строку поиска'})
    posts_search = (
        Post.objects.select_related('author').select_related('group')
        .filter(Q(text__contains=text)
                | Q(text__contains=text.lower())
                | Q(text__contains=text.capitalize())
                | Q(author__username__contains=text)
                | Q(author__first_name__contains=text)))
    context = get_paginator(request, posts_search)
    count_posts = context['page_obj'].paginator.count
    title = 'Результаты поиска' if count_posts else 'Ничего не найдено'
    context.update({'title': title})
    cache.clear()
    return render(request, 'posts/index.html', context)
