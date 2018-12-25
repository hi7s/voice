# coding=utf-8
# !/usr/bin/env python

from django.conf.urls import url
from django.contrib import admin, auth
from django.contrib import messages
from django.contrib.admin.options import IS_POPUP_VAR
from django.contrib.admin.sites import AdminSite
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.forms import AdminPasswordChangeForm
from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.http import HttpResponseRedirect, Http404
from django.shortcuts import get_object_or_404
from django.template.response import TemplateResponse
from django.utils.decorators import method_decorator
from django.utils.html import escape
from django.utils.translation import ugettext, ugettext_lazy as _
from django.utils.translation import ugettext as _
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.debug import sensitive_post_parameters

from blog.forms import PostsForm, UserChangeForm, UserCreationForm
from blog.models import Category, Link, Tag, TagGroup, Posts, Users, PostTag, Argument, Column, Comments, Pages
from mysite import settings

csrf_protect_m = method_decorator(csrf_protect)
sensitive_post_parameters_m = method_decorator(sensitive_post_parameters())


class MyModelAdmin(admin.ModelAdmin):
    pass


class PostTagInline(admin.StackedInline):
    model = PostTag
    extra = 2


class PostAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'author', 'category', 'post_date', 'post_status', 'weight', 'user_name',)
    list_display_links = ('title', 'user_name',)
    list_filter = ('post_status', 'category',)
    ordering = ('-post_date',)
    list_per_page = 20
    list_select_related = ('user',)
    search_fields = ('title', 'content',)
    actions = ('make_publish', 'make_private', 'set_excellent', 'revoke_excellent',)
    actions_on_top = False
    actions_on_bottom = True
    form = PostsForm
    date_hierarchy = 'post_date'
    radio_fields = {'post_status': admin.HORIZONTAL}
    view_on_site = True

    inlines = [PostTagInline]
    fieldsets = (
        (None, {
            'fields': (
                'title', 'content', 'category', 'post_status', 'post_date',
            )
        }),
        ('其他选项', {
            'classes': ('collapse',),
            'fields': (
                'note', 'author', 'source', 'weight',
            )
        }),
    )

    def view_on_site(self, obj):
        return '/article/%s/' % obj.id

    # actions
    def make_publish(self, request, queryset):
        rows_updated = queryset.update(post_status='publish')
        self.message_user(request, "【%s】条记录已成功设置发布" % rows_updated)

    make_publish.short_description = "设置发布"

    def make_private(self, request, queryset):
        rows_updated = queryset.update(post_status='private')
        self.message_user(request, "【%s】条记录已成功取消设置发布" % rows_updated)

    make_private.short_description = "取消设置发布"

    def set_excellent(self, request, queryset):
        rows_updated = queryset.update(weight=9)
        self.message_user(request, "【%s】条记录已成功设置推荐" % rows_updated)

    set_excellent.short_description = "设置推荐"

    def revoke_excellent(self, request, queryset):
        rows_updated = queryset.update(weight=0)
        self.message_user(request, "【%s】条记录已成功取消设置推荐" % rows_updated)

    revoke_excellent.short_description = "取消设置推荐"

    # columns
    def user_name(self, obj):
        return obj.user.user_nickname

    user_name.short_description = '发布人'

    def content_more(self, obj):
        return obj.content[0:200]

    content_more.short_description = '内容摘要'


class CommentAdmin(admin.ModelAdmin):
    list_display = (
        'comment_post_title', 'comment_content_more',
        'comment_author', 'comment_approved', 'comment_date',
    )
    list_display_links = ('comment_post_title',)
    actions = ('make_approve', 'make_reject',)
    radio_fields = {"comment_approved": admin.HORIZONTAL}
    view_on_site = True
    readonly_fields = ('comment_author', 'comment_date',)
    fieldsets = (
        (None, {
            'fields': (
                'comment_post', 'comment_content',
                'comment_author', 'comment_date', 'comment_approved',
            )
        }),
        ('其他选项', {
            'classes': ('collapse',),
            'fields': (
                'comment_author_email', 'comment_author_url', 'comment_author_ip', 'comment_date_gmt', 'comment_karma',
                'comment_agent', 'comment_type', 'comment_parent', 'user_id',
            )
        }),
    )

    def view_on_site(self, obj):
        return '/blog/?p=%d#comment-%d' % (obj.comment_post.id, obj.comment_id)

    def make_approve(self, request, queryset):
        rows_updated = queryset.update(comment_approved='1')
        message_bit = "%s 条记录已" % rows_updated
        self.message_user(request, "%s同意评论." % message_bit)

    make_approve.short_description = "同意评论"

    def make_reject(self, request, queryset):
        rows_updated = queryset.update(comment_approved='0')
        message_bit = "%s 条记录已" % rows_updated
        self.message_user(request, "%s不同意评论." % message_bit)

    make_reject.short_description = "不同意评论"

    def comment_post_id(self, obj):
        return obj.comment_post.id

    def comment_post_title(self, obj):
        return obj.comment_post.title

    comment_post_title.short_description = "评论文章标题"

    def comment_content_more(self, obj):
        return obj.comment_content[0:20]  # +u'更多'

    comment_content_more.short_description = '内容摘要'


class OptionsAdmin(admin.ModelAdmin):
    list_display = ('option_name', 'option_value', 'autoload',)
    list_editable = ('autoload',)


class TagAdmin(admin.ModelAdmin):
    list_display = ('no', 'name', 'slug', 'group', 'remark', 'created_at', 'visible',)
    list_display_links = ('no', 'name',)
    ordering = ('no',)
    list_per_page = 20
    radio_fields = {'visible': admin.HORIZONTAL}
    fieldsets = (
        (None, {
            'fields': (
                'no', 'name', 'slug', 'group', 'remark', 'visible',
            )
        }),
    )


class ArgumentAdmin(admin.ModelAdmin):
    list_display = ('no', 'key', 'value', 'remark', 'created_at', 'enable',)
    list_display_links = ('no', 'key',)
    ordering = ('no',)
    list_per_page = 20
    radio_fields = {'enable': admin.HORIZONTAL}
    fieldsets = (
        (None, {
            'fields': (
                'no', 'key', 'value', 'remark', 'enable',
            )
        }),
    )


class CategoryAdmin(admin.ModelAdmin):
    list_display = ('no', 'name', 'slug', 'remark', 'created_at', 'visible',)
    list_display_links = ('no', 'name',)
    ordering = ('no',)
    list_per_page = 20
    radio_fields = {'visible': admin.HORIZONTAL}
    fieldsets = (
        (None, {
            'fields': (
                'no', 'name', 'slug', 'icon', 'remark', 'visible',
            )
        }),
    )


class PagesAdmin(admin.ModelAdmin):
    list_display = ('no', 'slug', 'title', 'author', 'created_at', 'visible',)
    list_display_links = ('no', 'title',)
    list_filter = ('visible',)
    ordering = ('no',)
    list_per_page = 20
    form = PostsForm
    radio_fields = {'visible': admin.HORIZONTAL}
    fieldsets = (
        (None, {
            'fields': (
                'no', 'title', 'slug', 'content', 'author', 'remark', 'visible',
            )
        }),
    )


class TagGroupAdmin(admin.ModelAdmin):
    list_display = ('no', 'name', 'slug', 'remark', 'created_at', 'visible',)
    list_display_links = ('no', 'name',)
    ordering = ('no',)
    list_per_page = 20
    radio_fields = {'visible': admin.HORIZONTAL}
    fieldsets = (
        (None, {
            'fields': (
                'no', 'name', 'slug', 'remark', 'visible',
            )
        }),
    )


class PostTagAdmin(admin.ModelAdmin):
    list_display = ('post', 'tag')
    list_per_page = 20


class LinkAdmin(admin.ModelAdmin):
    list_display = ('no', 'name', 'url', 'target', 'remark', 'created_at', 'visible',)
    list_display_links = ('no', 'name',)
    radio_fields = {'visible': admin.HORIZONTAL, 'target': admin.HORIZONTAL}

    fieldsets = (
        (None, {
            'fields': (
                'no', 'name', 'url', 'visible', 'remark',
            )
        }),
        ('其他选项', {
            'classes': ('collapse',),
            'fields': (
                'logo', 'target', 'contact_user', 'contact_tel',
            )
        }),
    )


class ColumnAdmin(admin.ModelAdmin):
    list_display = ('no', 'name', 'url', 'target', 'remark', 'created_at', 'visible',)
    list_display_links = ('no', 'name',)
    radio_fields = {'visible': admin.HORIZONTAL, 'target': admin.HORIZONTAL}

    fieldsets = (
        (None, {
            'fields': (
                'no', 'name', 'url', 'icon', 'target', 'visible', 'remark',
            )
        }),
    )


class PermissionAdmin(admin.ModelAdmin):
    pass


class UserAdmin(admin.ModelAdmin):
    add_form_template = 'admin/auth/user/add_form.html'
    change_user_password_template = None
    fieldsets = (
        (None, {
            'fields': (
                'user_login', 'user_password',
            )
        }),
        (_('Personal info'), {
            'fields': (
                'user_email', 'user_url', 'user_nickname',
            )
        }),
        (_('Permissions'), {
            'fields': (
                'is_staff', 'is_superuser', 'user_status', 'groups', 'user_permissions',
            )
        }),
        (_('Important dates'), {
            'fields': (
                'last_login', 'user_registered',
            )
        }),
    )
    add_fieldsets = (
        (None, {
            'classes': (
                'wide',
            ),
            'fields': (
                'user_login', 'user_password',
            ),
        }),
    )
    form = UserChangeForm
    add_form = UserCreationForm
    change_password_form = AdminPasswordChangeForm
    list_display = ('user_login', 'user_email', 'is_staff',)
    list_filter = ('is_staff', 'is_superuser', 'groups',)  # 'is_active',
    search_fields = ('user_login', 'user_email',)
    ordering = ('user_login',)
    filter_horizontal = ('groups', 'user_permissions',)

    def is_active(self, obj):
        return self.user_status

    def get_fieldsets(self, request, obj=None):
        if not obj:
            return self.add_fieldsets
        return super(UserAdmin, self).get_fieldsets(request, obj)

    def get_form(self, request, obj=None, **kwargs):
        """
        Use special form during user creation
        """
        defaults = {}
        if obj is None:
            defaults['form'] = self.add_form
        defaults.update(kwargs)
        return super(UserAdmin, self).get_form(request, obj, **defaults)

    def get_urls(self):
        return [
                   url(r'^(\d+)/password/', self.admin_site.admin_view(self.user_change_password))
               ] + super(UserAdmin, self).get_urls()

    def lookup_allowed(self, lookup, value):
        if lookup.startswith('password'):
            return False
        return super(UserAdmin, self).lookup_allowed(lookup, value)

    @sensitive_post_parameters_m
    @csrf_protect_m
    @transaction.atomic
    def add_view(self, request, form_url='', extra_context=None):
        # It's an error for a user to have add permission but NOT change
        # permission for users. If we allowed such users to add users, they
        # could create superusers, which would mean they would essentially have
        # the permission to change users. To avoid the problem entirely, we
        # disallow users from adding users if they don't have change
        # permission.
        if not self.has_change_permission(request):
            if self.has_add_permission(request) and settings.DEBUG:
                # Raise Http404 in debug mode so that the user gets a helpful
                # error message.
                raise Http404(
                    'Your user does not have the "Change user" permission. In '
                    'order to add users, Django requires that your user '
                    'account have both the "Add user" and "Change user" '
                    'permissions set.')
            raise PermissionDenied
        if extra_context is None:
            extra_context = {}
        username_field = self.model._meta.get_field(self.model.USERNAME_FIELD)
        defaults = {
            'auto_populated_fields': (),
            'username_help_text': username_field.help_text,
        }
        extra_context.update(defaults)
        return super(UserAdmin, self).add_view(request, form_url, extra_context)

    @sensitive_post_parameters_m
    def user_change_password(self, request, id, form_url=''):
        if not self.has_change_permission(request):
            raise PermissionDenied
        user = get_object_or_404(self.get_queryset(request), pk=id)
        if request.method == 'POST':
            form = self.change_password_form(user, request.POST)
            if form.is_valid():
                form.save()
                change_message = self.construct_change_message(request, form, None)
                self.log_change(request, user, change_message)
                msg = ugettext('Password changed successfully.')
                messages.success(request, msg)
                update_session_auth_hash(request, form.user)
                return HttpResponseRedirect('..')
        else:
            form = self.change_password_form(user)

        fieldsets = [(None, {'fields': list(form.base_fields)})]
        admin_form = admin.helpers.AdminForm(form, fieldsets, {})

        context = {
            'title': _('Change password: %s') % escape(user.get_username()),
            'adminForm': admin_form,
            'form_url': form_url,
            'form': form,
            'is_popup': (IS_POPUP_VAR in request.POST or IS_POPUP_VAR in request.GET),
            'add': True,
            'change': False,
            'has_delete_permission': False,
            'has_change_permission': True,
            'has_absolute_url': False,
            'opts': self.model._meta,
            'original': user,
            'save_as': False,
            'show_save': True,
        }
        context.update(admin.site.each_context())
        return TemplateResponse(
            request,
            self.change_user_password_template or 'admin/auth/user/change_password.html',
            context
        )

    def response_add(self, request, obj, post_url_continue=None):
        """
        Determines the HttpResponse for the add_view stage. It mostly defers to
        its superclass implementation but is customized because the User model
        has a slightly different workflow.
        """
        # We should allow further modification of the user just added i.e. the
        # 'Save' button should behave like the 'Save and continue editing'
        # button except in two scenarios:
        # * The user has pressed the 'Save and add another' button
        # * We are adding a user in a popup
        if '_add_another' not in request.POST and IS_POPUP_VAR not in request.POST:
            request.POST['_continue'] = 1
        return super(UserAdmin, self).response_add(request, obj, post_url_continue)


class MyAdminSite(AdminSite):
    site_header = '网站后台管理系统'
    site_title = '网站后台管理系统'
    index_title = 'JustOK'
    title = 'JustOK'

    def __init__(self, name='admin'):
        super(MyAdminSite, self).__init__(name)


AdminSite.site_header = '网站后台管理系统'
AdminSite.site_title = '网站后台管理系统'
AdminSite.title = 'JustOK'
admin.site = MyAdminSite()

admin.site.register(auth.models.Group)
admin.site.register(auth.models.Permission, PermissionAdmin)

admin.site.register(Users, UserAdmin)
admin.site.register(Posts, PostAdmin)
admin.site.register(Argument, ArgumentAdmin)
admin.site.register(Link, LinkAdmin)
admin.site.register(Column, ColumnAdmin)
admin.site.register(Tag, TagAdmin)
admin.site.register(TagGroup, TagGroupAdmin)
admin.site.register(Category, CategoryAdmin)
admin.site.register(Pages, PagesAdmin)

admin.site.register(Comments, CommentAdmin)
