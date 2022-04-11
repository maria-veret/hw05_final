from datetime import datetime

from django.core.paginator import Paginator
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, HttpResponse
from django.conf import settings
from django.views.decorators.cache import cache_page

from .models import Post, Group, User, Follow
from .forms import PostForm, CommentForm


@cache_page(20)
def index(request: HttpRequest) -> HttpResponse:
    """Функция для главной страницы.
    """
    template = 'posts/index.html'
    post_list = Post.objects.all()
    paginator = Paginator(post_list, settings.PAGE)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    title = 'Последние обновления на сайте'
    context = {
        'page_obj': page_obj,
        'title': title,
    }
    return render(request, template, context)


def group_posts(request: HttpRequest, slug: str) -> HttpResponse:
    """Функция для записей сообщества.
    """
    template = 'posts/group_list.html'
    group = get_object_or_404(Group, slug=slug)
    posts = Post.objects.filter(group=group)
    paginator = Paginator(posts, settings.PAGE)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    title = f'Записи сообщества {group}'
    context = {
        'group': group,
        'posts': posts,
        'page_obj': page_obj,
        'title': title,
    }
    return render(request, template, context)


def profile(request: HttpRequest, username: str) -> HttpResponse:
    """Функция для профайла пользователя.
    """
    template = 'posts/profile.html'
    author = get_object_or_404(User, username=username)
    posts = author.posts.all()
    count_posts = author.posts.count()
    paginator = Paginator(posts, settings.PAGE)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    following = request.user.is_authenticated
    if following:
        following = author.following.filter(user=request.user).exists()
    title = f'Профайл пользователя {author}'
    context = {
        'author': author,
        'posts': posts,
        'count_posts': count_posts,
        'page_obj': page_obj,
        'title': title,
        'following': following
    }
    return render(request, template, context)


def post_detail(request: HttpRequest, post_id: int) -> HttpResponse:
    """Функция для просмотра записи.
    """
    template = 'posts/post_detail.html'
    post = get_object_or_404(Post, id=post_id)
    group = post.group
    author = post.author
    count_posts = author.posts.count()
    comments = post.comments.all()
    form = CommentForm()
    title = f'Пост {post.text[:30]}'
    context = {
        'form': form,
        'comments': comments,
        'post': post,
        'group': group,
        'count_posts': count_posts,
        'title': title,
    }
    return render(request, template, context)


@login_required
def post_create(request: HttpRequest) -> HttpResponse:
    """Функция для публикации постов.
    """
    template = 'posts/create_post.html'
    title = 'Создание поста'
    if request.method != 'POST':
        form = PostForm()
        context = {
            'form': form,
            'title': title,
        }
        return render(request, template, context)
    form = PostForm(
        request.POST or None,
        files=request.FILES or None
    )
    if not form.is_valid():
        context = {
            'form': form,
            'title': title,
        }
        return render(request, template, context)
    post = form.save(commit=False)
    post.author = request.user
    post.pub_date = datetime.now()
    post.save()
    return redirect('posts:profile', request.user)


@login_required
def post_edit(request: HttpRequest, post_id: int) -> HttpResponse:
    """Функция для редактирования постов.
    """
    template = 'posts/update_post.html'
    post = get_object_or_404(Post, id=post_id, author=request.user)
    title = f'Редактрирование поста {post.id}'
    form = PostForm(instance=post)
    if request.method != 'POST':
        context = {
            'form': form,
            'is_edit': True,
            'post': post,
            'title': title,
        }
        return render(request, template, context)
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post
    )
    if not form.is_valid():
        context = {
            'form': form,
            'is_edit': True,
            'title': title,
        }
        return render(request, template, context)
    post = form.save(commit=False)
    post.author = request.user
    post.pub_date = datetime.now()
    post.save()
    return redirect('posts:post_detail', post.id)


@login_required
def add_comment(request: HttpRequest,
                post_id: int) -> HttpResponse:
    form = CommentForm(request.POST or None)
    post = get_object_or_404(Post, id=post_id)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post.id)


@login_required
def follow_index(request):
    title = 'Подписки'
    posts = Post.objects.filter(
        author__following__user=request.user)
    paginator = Paginator(posts, settings.PAGE)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'page_obj': page_obj,
        'title': title,
    }
    return render(request, 'posts/follow.html', context)


@login_required
def profile_follow(request, username):
    author = get_object_or_404(User, username=username)
    if author != request.user:
        Follow.objects.get_or_create(user=request.user, author=author)
    return redirect('posts:profile', username=author.username)


@login_required
def profile_unfollow(request, username):
    author = get_object_or_404(User, username=username)
    Follow.objects.filter(user=request.user, author=author).delete()
    return redirect('posts:profile', username=author.username)
