# coding=utf-8
# !/usr/bin/env python

from django.core.paginator import Paginator, Page
from django.db.models import Count
from django.db.models import Q
from django.shortcuts import render_to_response
from django.template.loader import render_to_string
from django.views.decorators.cache import cache_page

from blog.models import Manager, Posts, Comments, Category, Link, Column, PostTag, Tag, Pages

PAGE_SIZE = 15

CACHE_TIMEOUT = 30

manager = Manager()


# show article list by category
@cache_page(CACHE_TIMEOUT)
def category(request, slug):
    current_category = Category.objects.filter(slug=slug).first()
    post_list = Posts.objects.filter(category__slug=slug, post_status='publish', ).order_by('post_date')[:PAGE_SIZE]
    context = {
        'posts': post_list,
        'title': current_category.name,
        'category': current_category,
    }
    context = union_context(context)
    return render_to_response('article_list.html', context)


# show article list by date
@cache_page(CACHE_TIMEOUT)
def latest(request):
    post_list = Posts.objects.filter(post_status='publish', ).order_by('-post_date')[:PAGE_SIZE]
    context = {
        'posts': post_list,
        'title': '最新',
    }
    context = union_context(context)
    return render_to_response('article_list.html', context)


# show article list by weight
@cache_page(CACHE_TIMEOUT)
def favorite(request):
    post_list = Posts.objects.all().filter(post_status='publish', weight=9, ).order_by('-post_date')[:PAGE_SIZE]
    context = {
        'posts': post_list,
        'title': '推荐',
    }
    context = union_context(context)
    return render_to_response('article_list.html', context)


# show article list by keywords
@cache_page(CACHE_TIMEOUT * 5)
def search(request):
    s = request.GET.get('s')
    posts_list = []
    if s is not None:
        posts_list = Posts.objects.all().filter(
            post_status='publish',
        ).filter(Q(title__contains=s) | Q(content__contains=s)).order_by('-post_date')[:PAGE_SIZE]
    context = {
        'title': u'搜索：%s' % s,
        'posts': posts_list,
    }
    context = union_context(context)
    return render_to_response('article_list.html', context)


# show article detail by id
@cache_page(CACHE_TIMEOUT)
def article(request, post_id):
    post = Posts.objects.filter(id=post_id).first()
    title = post.title
    prev_post = Posts.objects.all().filter(id__lt=post.id, category_id=post.category.id, ).only('id', 'title', ).last()
    next_post = Posts.objects.all().filter(id__gt=post.id, category_id=post.category.id, ).only('id', 'title', ).first()
    if post.author:
        title = u'%s - %s' % (post.title, post.author)
    context = {
        'post': post,
        'title': title,
        'prev_post': prev_post,
        'next_post': next_post,
    }
    context = union_context(context)
    return render_to_response('article_info.html', context)


# show page info by slug
@cache_page(CACHE_TIMEOUT)
def page(request, slug):
    _page = Pages.objects.filter(slug=slug).first()
    title = _page.title
    if _page.author:
        title = u'%s - %s' % (_page.title, _page.author)
    context = {
        'page': _page,
        'title': title,
    }
    context = union_context(context)
    return render_to_response('page_info.html', context)


# archive
@cache_page(CACHE_TIMEOUT)
def archive(request):
    context = {
        'title': u'归档',
    }
    context = union_context(context)
    return render_to_response('calendar.html', context)


# show article list by tag
@cache_page(CACHE_TIMEOUT)
def tag(request, slug):
    post_list = Posts.objects.filter(
        tags__slug=slug, post_status='publish',
    ).order_by('-post_date', )[:PAGE_SIZE]
    current_tag = Tag.objects.filter(slug=slug).first()
    context = {
        'title': u'标签：%s' % current_tag.name,
        'posts': post_list,
    }
    context = union_context(context)
    return render_to_response('article_list.html', context)


# show article list by year
@cache_page(CACHE_TIMEOUT)
def archive_by_year(request, year):
    post_list = Posts.objects.all().filter(
        post_status='publish', post_date__year=year,
    ).order_by('post_date', )[:PAGE_SIZE]
    context = {
        'title': u'归档：%s年' % year,
        'posts': post_list,
    }
    context = union_context(context)
    return render_to_response('article_list.html', context)


# show article list by month
@cache_page(CACHE_TIMEOUT)
def archive_by_month(request, year, month):
    post_list = Posts.objects.all().filter(
        post_status='publish', post_date__year=year, post_date__month=month,
    ).order_by('post_date', )[:PAGE_SIZE]
    context = {
        'title': u'归档：%s年%s月' % (year, month),
        'posts': post_list,
    }
    context = union_context(context)
    return render_to_response('article_list.html', context)


# show article list by random
def random(request):
    post_list = Posts.objects.filter(post_status='publish', ).order_by('?', )[:PAGE_SIZE]
    context = {
        'posts': post_list,
        'title': '随便看看',
    }
    context = union_context(context)
    return render_to_response('article_list.html', context)


def union_context(context):
    # column list
    column_list = Column.objects.all().filter(visible='Y', ).order_by('no', )
    # month list
    select = {
        'year': 'year(post_date)',
        'month': 'substr(post_date, 6, 2)',
        'key': 'substr(post_date, 1, 7)',
    }
    month_list = Posts.objects.filter(
        post_status='publish',
    ).extra(select=select).values('year', 'month', 'key', ).annotate(Count('id')).order_by('-key', )
    # category list
    category_list = Posts.objects.filter(
        post_status='publish',
    ).values(
        'category_id', 'category__name', 'category__slug', 'category__icon',
    ).annotate(Count('id')).order_by('category__no', )
    # tag list
    tag_list = PostTag.objects.filter(
        post__post_status='publish',
    ).values(
        'tag_id', 'tag__slug', 'tag__name',
    ).annotate(Count('post_id', )).order_by('-post_id__count', 'tag__slug', )[:30]
    # link list
    link_list = Link.objects.filter(visible='Y').order_by('no')
    # result context
    result_context = {
        'columns': column_list,
        'months': month_list,
        'categories': category_list,
        'tags': tag_list,
        'links': link_list,
    }
    # external context
    for k in context:
        if k in result_context:
            continue
        result_context[k] = context[k]
    return result_context


def feed(request):
    context = {}
    return render_to_response('test.html', context)


# Paging navigator
class MyPaginator(Paginator):
    def __init__(self, object_list, per_page, range_num=5, orphans=0, allow_empty_first_page=True):
        self.range_num = range_num
        Paginator.__init__(self, object_list, per_page, orphans, allow_empty_first_page)

    def page(self, number):
        self.page_number = number
        return super(MyPaginator, self).page(number)

    def _get_page_range_ext(self):
        page_range = super(MyPaginator, self).page_range
        start = long(self.page_number) - 1 - self.range_num / 2
        end = long(self.page_number) + self.range_num / 2
        if start <= 0:
            end = end - start
            start = 0
        return list(page_range)[start:end]

    page_range_ext = property(_get_page_range_ext)


class MyPage(Page):
    def __init__(self, page):
        super(MyPage, self).__init__(page.object_list, page.number, page.paginator)
        self.object_list = page.object_list

    def _next(self):
        return self.object_list[super(MyPage, self).next_page_number()]

    def _prev(self):
        return self.object_list[super(MyPage, self).previous_page_number()]

    next = property(_next)
    prev = property(_prev)
