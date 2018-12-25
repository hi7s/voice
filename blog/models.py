import datetime
import os

from ckeditor.fields import RichTextField
from django.contrib.auth.hashers import (check_password, make_password, is_password_usable)
from django.contrib.auth.models import AbstractBaseUser
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.models import (BaseUserManager, AbstractBaseUser, PermissionsMixin)
from django.core.mail import send_mail
from django.core.urlresolvers import reverse
from django.db import models
from django.utils import timezone
from django.utils.crypto import salted_hmac
from django.utils.translation import ugettext_lazy as _

db_prefix = 'wp_'
db_managed = True

USER_STATUS = (
    (1, 'active'),
    (0, 'inactive'),
)
STATUS = (
    ('closed', u'关闭'),
    ('open', u'打开'),
)
POST_STATUS = (
    ('draft', u'草稿'),
    ('inherit', u'继承'),
    ('private', u'私有'),
    ('publish', u'已发布'),
)
POST_TYPE = (
    ('post', u'文章'),
    ('revision', u'修订版'),
    ('page', u'页面'),
    ('attachment', u'附件'),
    ('nav_menu_item', u'导航菜单'),
)
POST_MIME_TYPE = (
    ('text/html', 'text/html'),
    ('markdown', 'markdown'),
    ('image/gif', 'image/gif'),
    ('text/plain', 'text/plain'),
)
APPROVED_TYPE = (
    ('1', u'同意'),
    ('0', u'未审核'),
    ('spam', u'垃圾'),
    ('trash', u'回收站'),
)
TAXONOMY_TYPE = (
    ('category', u'文章分类'),
    ('post_tag', u'文章标签'),
    ('post_format', 'post_format'),
    ('link_category', u'链接分类'),
)
VISIBLE_TYPE = (
    ('Y', u'启用'),
    ('N', u'关闭'),
)
TARGET_TYPE = (
    ('_self', u'同窗口'),
    ('_blank', u'新窗口'),
    ('_top', u'弹出'),
)


class DjangoMigrations(models.Model):
    id = models.IntegerField(primary_key=True)  # AutoField?
    app = models.CharField(max_length=255)
    name = models.CharField(max_length=255)
    applied = models.DateTimeField()

    class Meta:
        managed = db_managed
        db_table = 'django_migration'


class Options(models.Model):
    option_id = models.AutoField(primary_key=True)
    option_name = models.CharField(verbose_name=u'名称', unique=True, max_length=64)
    option_value = models.TextField(verbose_name=u'值')
    autoload = models.CharField(verbose_name=u'自动加载', default='', blank=True, max_length=20)

    class Meta:
        managed = db_managed
        db_table = db_prefix + 'option'
        verbose_name = u'可选'
        verbose_name_plural = u'可选管理'

    def __unicode__(self):
        return u'id[%s] %s' % (self.option_id, self.option_name)


class UserMeta(models.Model):
    id = models.BigIntegerField(primary_key=True)
    user = models.BigIntegerField()
    key = models.CharField(max_length=255, blank=True)
    value = models.TextField(blank=True)

    class Meta:
        managed = db_managed
        db_table = db_prefix + 'user_meta'


class MyUserManager(BaseUserManager):
    def _create_user(self, user_login, user_email, user_password,
                     is_staff, is_superuser, **extra_fields):
        if not user_login:
            raise ValueError('Users must have an user name')

        user = self.model(
            user_email=self.normalize_email(user_email),
            user_login=user_login,
            is_staff=is_staff,
            is_superuser=is_superuser,
            user_status=1,
        )

        user.set_password(user_password)
        user.save(using=self._db)
        return user

    def create_user(self, user_login, user_email=None, password=None, **extra_fields):
        return self._create_user(user_login, user_email, password, False, False,
                                 **extra_fields)

    def create_superuser(self, user_login, user_email, password, **extra_fields):
        return self._create_user(user_login, user_email, password, True, True,
                                 **extra_fields)


class MyAbstractBaseUser(models.Model):
    REQUIRED_FIELDS = []

    class Meta:
        abstract = True

    def get_username(self):
        "Return the identifying username for this User"
        return getattr(self, self.USERNAME_FIELD)

    def __str__(self):
        return self.get_username()

    def natural_key(self):
        return (self.get_username())

    @property
    def is_anonymous(self):
        """
        Always returns False. This is a way of comparing User objects to
        anonymous users.
        """
        return False

    @property
    def is_authenticated(self):
        """
        Always return True. This is a way to tell if the user has been
        authenticated in templates.
        """
        return True

    def has_usable_password(self):
        return is_password_usable(self.user_password)

    def get_full_name(self):
        raise NotImplementedError('subclasses of AbstractBaseUser must provide a get_full_name() method')

    def get_short_name(self):
        raise NotImplementedError('subclasses of AbstractBaseUser must provide a get_short_name() method.')

    def get_session_auth_hash(self):
        """
        Returns an HMAC of the password field.
        """
        key_salt = "django.contrib.auth.models.AbstractBaseUser.get_session_auth_hash"
        return salted_hmac(key_salt, self.user_password).hexdigest()


class Users(MyAbstractBaseUser, PermissionsMixin):
    id = models.AutoField(primary_key=True, unique=True)
    user_login = models.CharField(max_length=60, unique=True, verbose_name=u'登录名')
    user_password = models.CharField(max_length=164, verbose_name=u'密码')
    user_nickname = models.CharField(max_length=50, blank=True, verbose_name=u'昵称')
    user_email = models.CharField(max_length=100, blank=True, verbose_name='email')
    user_url = models.CharField(max_length=100, blank=True, verbose_name=u'网站')
    user_registered = models.DateTimeField(default=timezone.now, blank=True, verbose_name=u'注册时间')
    user_activation_key = models.CharField(max_length=60, blank=True)
    user_status = models.IntegerField(choices=USER_STATUS, default=0, verbose_name=u'状态', blank=True)
    display_name = models.CharField(max_length=250, blank=True, verbose_name=u'显示名字')

    # is_active = models.BooleanField(default=True)
    # is_admin = models.BooleanField(default=False)
    is_staff = models.BooleanField(_('staff status'), default=False, blank=True)
    last_login = models.DateTimeField(_('last login'), default=timezone.now, blank=True)

    USERNAME_FIELD = 'user_login'
    REQUIRED_FIELDS = ['user_email']

    objects = MyUserManager()

    def set_password(self, raw_password):
        self.user_password = make_password(raw_password)

    def check_password(self, raw_password):
        """
        Returns a boolean of whether the raw_password was correct. Handles
        hashing formats behind the scenes.
        """

        def setter(raw_password):
            self.set_password(raw_password)
            self.save(update_fields=["user_password"])

        return check_password(raw_password, self.user_password, setter)

    def set_unusable_password(self):
        # Sets a value that will never be a valid hash
        self.user_password = make_password(None)

    #############

    def get_full_name(self):
        # The user is identified by their email address
        return self.user_nickname

    def get_short_name(self):
        # The user is identified by their email address
        return self.display_name

    def email_user(self, subject, message, from_email=None, **kwargs):
        """ 
        Sends an email to this User.
        """
        send_mail(subject, message, from_email, [self.email], **kwargs)

    @property
    def is_active(self):
        return self.user_status

    def __unicode__(self):
        return u'%s' % (self.user_nickname)
        # return u'id['+str(self.id)+'] '+self.user_nickname

    class Meta:
        managed = db_managed
        db_table = db_prefix + 'user'
        verbose_name = u'用户'
        verbose_name_plural = u'用户管理'


class Column(models.Model):
    id = models.AutoField(primary_key=True)
    no = models.CharField(max_length=20, verbose_name=u'编号')
    name = models.CharField(max_length=50, verbose_name=u'名称')
    url = models.CharField(max_length=100, verbose_name=u'URL链接')
    icon = models.CharField(max_length=50, verbose_name=u'图标', blank=True)
    target = models.CharField(default='_self', max_length=25, choices=TARGET_TYPE, verbose_name=u'打开方式')
    remark = models.CharField(blank=True, max_length=200, verbose_name=u'备注')
    created_at = models.DateTimeField(default=datetime.datetime.now, blank=True, verbose_name=u'添加日期')
    visible = models.CharField(default='Y', max_length=20, choices=VISIBLE_TYPE, verbose_name=u'是否可见')

    def __unicode__(self):
        return u'%s' % self.name

    class Meta:
        managed = db_managed
        db_table = db_prefix + 'column'
        ordering = ('no',)
        verbose_name = u'栏目'
        verbose_name_plural = u'栏目管理'


class Argument(models.Model):
    id = models.AutoField(primary_key=True)
    no = models.CharField(max_length=20, verbose_name=u'编号')
    key = models.CharField(unique=True, max_length=50, verbose_name=u'键')
    value = models.CharField(max_length=50, verbose_name=u'值')
    remark = models.CharField(max_length=200, blank=True, verbose_name=u'备注')
    created_at = models.DateTimeField(default=datetime.datetime.now, blank=True, verbose_name=u'添加日期')
    enable = models.CharField(default='Y', blank=True, max_length=20, choices=VISIBLE_TYPE, verbose_name=u'是否启用')

    def __unicode__(self):
        return u'%s' % self.key

    class Meta:
        managed = db_managed
        db_table = db_prefix + 'argument'
        ordering = ('no',)
        verbose_name = u'参数'
        verbose_name_plural = u'参数管理'


class Category(models.Model):
    id = models.AutoField(primary_key=True)
    no = models.CharField(max_length=20, verbose_name=u'编号')
    name = models.CharField(max_length=50, verbose_name=u'名称')
    slug = models.CharField(unique=True, max_length=50, verbose_name=u'别名')
    icon = models.CharField(max_length=50, verbose_name=u'图标', blank=True)
    remark = models.CharField(max_length=200, blank=True, verbose_name=u'备注')
    created_at = models.DateTimeField(default=datetime.datetime.now, blank=True, verbose_name=u'添加日期')
    visible = models.CharField(default='Y', blank=True, max_length=20, choices=VISIBLE_TYPE, verbose_name=u'是否可见')

    def __unicode__(self):
        return u'%s' % self.name

    class Meta:
        managed = db_managed
        db_table = db_prefix + 'category'
        ordering = ('no',)
        verbose_name = u'类目'
        verbose_name_plural = u'类目管理'


class TagGroup(models.Model):
    id = models.AutoField(primary_key=True)
    no = models.CharField(max_length=20, verbose_name=u'编号')
    name = models.CharField(max_length=50, verbose_name=u'名称')
    slug = models.CharField(unique=True, max_length=50, verbose_name=u'别名')
    remark = models.CharField(max_length=200, blank=True, verbose_name=u'备注')
    created_at = models.DateTimeField(default=datetime.datetime.now, blank=True, verbose_name=u'添加日期')
    visible = models.CharField(default='Y', max_length=1, choices=VISIBLE_TYPE, verbose_name=u'是否可见')

    def __unicode__(self):
        return u'%s' % self.name

    class Meta:
        managed = db_managed
        db_table = db_prefix + 'tag_group'
        verbose_name = u'标签组'
        verbose_name_plural = u'标签组管理'


class Tag(models.Model):
    id = models.AutoField(primary_key=True)
    no = models.CharField(max_length=20, verbose_name=u'编号')
    name = models.CharField(max_length=50, verbose_name=u'名称')
    slug = models.CharField(unique=True, max_length=50, verbose_name=u'别名')
    group = models.ForeignKey(TagGroup, verbose_name=u'组别')
    remark = models.CharField(max_length=200, blank=True, verbose_name=u'备注')
    created_at = models.DateTimeField(default=datetime.datetime.now, blank=True, verbose_name=u'添加日期')
    visible = models.CharField(default='Y', max_length=1, choices=VISIBLE_TYPE, verbose_name=u'是否可见')

    def __unicode__(self):
        return u'%s' % self.name

    class Meta:
        managed = db_managed
        db_table = db_prefix + 'tag'
        ordering = ('no',)
        verbose_name = u'标签'
        verbose_name_plural = u'标签管理'


class Posts(models.Model):
    id = models.AutoField(verbose_name=u'编号', primary_key=True)
    user = models.ForeignKey(Users, verbose_name=u'发布人', default='1')
    category = models.ForeignKey(Category, verbose_name=u'类目', default='1')
    title = models.CharField(max_length=120, verbose_name=u'标题')
    content = RichTextField(verbose_name=u'内容')
    note = RichTextField(verbose_name=u'注释', default='', blank=True)
    author = models.CharField(verbose_name=u'作者', default='', blank=True, max_length=20)
    weight = models.IntegerField(verbose_name=u'权重', default=0, blank=True)
    post_date = models.DateTimeField(verbose_name=u'发布时间', default=datetime.datetime.now, blank=True)
    post_date_gmt = models.DateTimeField(default=timezone.now, blank=True)
    post_excerpt = models.TextField(default='', blank=True)
    post_status = models.CharField(verbose_name=u'发布状态', default='publish', choices=POST_STATUS, max_length=20)
    source = models.CharField(verbose_name=u'来源', default='', blank=True, max_length=20)
    comment_status = models.CharField(default='', blank=True, max_length=20)
    ping_status = models.CharField(verbose_name=u'ping状态', default='', blank=True, max_length=20)
    post_password = models.CharField(default='', blank=True, max_length=20)
    post_name = models.CharField(default='', blank=True, max_length=200)
    to_ping = models.TextField(default='', blank=True)
    pinged = models.TextField(default='', blank=True)
    post_modified = models.DateTimeField(verbose_name=u'修改时间', default=datetime.datetime.now, blank=True)
    post_modified_gmt = models.DateTimeField(default=timezone.now, blank=True)
    guid = models.CharField(max_length=255, default='', blank=True)
    comment_count = models.BigIntegerField(default=0, blank=True)
    tags = models.ManyToManyField(Tag, through='PostTag')

    def __unicode__(self):
        return u'%s' % self.title

    def get_absolute_url(self):
        return reverse('blog.views.article', args=[str(self.id)])

    class Meta:
        managed = db_managed
        db_table = db_prefix + 'post'
        verbose_name = u'内容'
        verbose_name_plural = u'内容管理'


class PostTag(models.Model):
    id = models.AutoField(primary_key=True)
    post = models.ForeignKey(Posts, verbose_name=u'内容')
    tag = models.ForeignKey(Tag, verbose_name=u'标签')

    def __unicode__(self):
        return u'%s' % self.post_id

    class Meta:
        managed = db_managed
        db_table = db_prefix + 'post_tag'
        verbose_name = u'标签'
        verbose_name_plural = u'标签管理'


class PostMeta(models.Model):
    id = models.AutoField(primary_key=True)
    post = models.ForeignKey(Posts, db_column='post_id')
    key = models.CharField(max_length=255, blank=True)
    value = models.TextField(blank=True)

    def __unicode__(self):
        return u'%s' % (self.id)

    class Meta:
        managed = db_managed
        db_table = db_prefix + 'post_meta'
        verbose_name = u'发布附带'
        verbose_name_plural = u'发布管理'


class CommentMeta(models.Model):
    id = models.BigIntegerField(primary_key=True)
    comment = models.BigIntegerField()
    key = models.CharField(max_length=255, blank=True)
    value = models.TextField(blank=True)

    class Meta:
        managed = db_managed
        db_table = db_prefix + 'comment_meta'


class Comments(models.Model):
    comment_id = models.AutoField(primary_key=True)
    comment_post = models.ForeignKey(Posts, verbose_name=u'文章')
    comment_author = models.CharField(max_length=100, verbose_name=u'评论者')
    comment_author_email = models.CharField(max_length=100)
    comment_author_url = models.CharField(max_length=200, blank=True)
    comment_author_ip = models.CharField(default='', max_length=100, blank=True)  # Field name made lowercase.
    comment_date = models.DateTimeField(verbose_name=u'评论日期', default=datetime.datetime.now, blank=True)
    comment_date_gmt = models.DateTimeField(default=timezone.now, blank=True)
    comment_content = models.TextField(verbose_name=u'评论内容')
    comment_karma = models.IntegerField(default=0)
    comment_approved = models.CharField(verbose_name=u'审核情况', choices=APPROVED_TYPE, max_length=20, default=0)
    comment_agent = models.CharField(default='', max_length=255, blank=True)
    comment_type = models.CharField(default='', max_length=20, blank=True)
    comment_parent = models.BigIntegerField(default=0)
    user_id = models.BigIntegerField(default=0)

    def get_absolute_url(self):
        return '/article/%d#comment-%d' % (self.comment_post.id, self.comment_id)

    class Meta:
        managed = db_managed
        db_table = db_prefix + 'comment'
        verbose_name = u'评论'
        verbose_name_plural = u'评论管理'

        permissions = (
            ("can_comment_direct", "can_comment_direct"),
            ("can_comment_unlimit_time", u'不限制时间评论')

        )

    def __unicode__(self):
        return u'%s' % (self.comment_id)


class Link(models.Model):
    id = models.AutoField(primary_key=True)
    no = models.CharField(max_length=20, verbose_name=u'编号')
    name = models.CharField(max_length=50, verbose_name=u'名称')
    url = models.CharField(max_length=100, verbose_name=u'URL链接')
    logo = models.CharField(max_length=100, blank=True, verbose_name='LOGO')
    target = models.CharField(default='_blank', max_length=25, choices=TARGET_TYPE, verbose_name=u'打开方式')
    contact_user = models.CharField(max_length=50, blank=True, verbose_name=u'联系人')
    contact_tel = models.CharField(max_length=50, blank=True, verbose_name=u'联系电话')
    remark = models.CharField(blank=True, max_length=200, verbose_name=u'备注')
    created_at = models.DateTimeField(default=datetime.datetime.now, blank=True, verbose_name=u'添加日期')
    visible = models.CharField(default='Y', max_length=20, choices=VISIBLE_TYPE, verbose_name=u'是否可见')

    class Meta:
        managed = db_managed
        db_table = db_prefix + 'link'
        verbose_name = u'链接'
        verbose_name_plural = u'链接管理'

    def __unicode__(self):
        return u'%s' % self.name


class Pages(models.Model):
    id = models.AutoField(primary_key=True)
    no = models.CharField(max_length=20, verbose_name=u'编号')
    title = models.CharField(max_length=50, verbose_name=u'标题')
    slug = models.CharField(max_length=50, verbose_name=u'别名')
    content = RichTextField(max_length=2000, verbose_name=u'内容')
    source = models.CharField(max_length=50, blank=True, verbose_name=u'来源')
    author = models.CharField(max_length=50, blank=True, verbose_name=u'作者')
    remark = models.CharField(blank=True, max_length=200, verbose_name=u'备注')
    created_at = models.DateTimeField(default=datetime.datetime.now, blank=True, verbose_name=u'添加日期')
    visible = models.CharField(default='Y', max_length=20, choices=VISIBLE_TYPE, verbose_name=u'是否可见')

    class Meta:
        managed = db_managed
        db_table = db_prefix + 'page'
        verbose_name = u'单页'
        verbose_name_plural = u'单页管理'

    def __unicode__(self):
        return u'%s' % self.title


class PostLinkManager(models.Manager):
    def get_queryset(self):
        ret = super(PostLinkManager, self).get_queryset().filter()
        return ret


# manager all models
class Manager(object):
    """docstring for Manager"""

    def __new__(cls, *args, **kwargs):
        # print '#####new'
        if not hasattr(cls, '_instance'):
            o = super(Manager, cls)
            # print 'new',type(o),type(cls),cls
            cls._instance = o.__new__(cls, *args, **kwargs)
            cls.instances = {}
            # print 'type:',cls
        return cls._instance

    def _get_class(self, cls=''):
        module_name = ''
        class_name = ''
        ws = cls.rsplit('.', 1)
        if len(ws) == 2:
            (module_name, class_name) = ws
        else:
            class_name = ws[0]
            module_name = __file__ and os.path.splitext(os.path.basename(__file__))[0]
        print module_name
        module_meta = __import__(module_name, globals(), locals(), [class_name])
        # print 'module_meta:',module_meta,' class_name:',class_name
        class_meta = getattr(module_meta, class_name)
        cls = class_meta
        return cls

    def __init__(self, cls=None, *args, **kwargs):
        self.cls = cls
        self.args = args
        self.kwargs = kwargs
        if cls is None:
            return
        if isinstance(cls, str):
            cls = self._get_class(cls)
        elif isinstance(cls, cls.__class__):
            self.instances[cls.__class__] = cls
            self.cls = cls.__class__
            return
        if cls in self.instances:
            self = self.instances[cls]
        else:
            obj = cls(*args, **kwargs)
            self.instances[cls] = obj
            self = obj

    def instance(self, cls=None, *args, **kwargs):
        # print 'membermethod'
        try:
            if cls is None:
                if self.cls is None:
                    return self
                cls = self.cls
            if isinstance(cls, str):
                cls = self._get_class(cls)
            if cls in self.instances:
                return self.instances[cls]
            else:
                # print 'instance no found',type(cls),args,kwargs
                obj = cls(*args, **kwargs)
                self.instances[cls] = obj
                return obj
        except TypeError, e:
            return cls
        except AttributeError, e:
            return cls
        except Exception, e:
            return e

    @classmethod
    def inst(cls, clz=None, *args, **kwargs):
        if clz is None:
            if cls is None:
                return cls()
            clz = cls
        return cls(clz, *args, **kwargs).instance(*args, **kwargs)

    @staticmethod
    def ins(cls=None, *args, **kwargs):
        return Manager(cls, *args, **kwargs).inst(cls, *args, **kwargs)

    @classmethod
    def add_member_method(self, cls, fun, *args, **kwargs):
        obj = self.instance(cls, *args, **kwargs);
        setattr(obj, fun.__name__, type.MethodType(fun, obj))
        return obj

    @classmethod
    def add_static_method(self, cls, fun, *args, **kwargs):
        obj = self.instance(cls, *args, **kwargs)
        setattr(obj, fun.__name__, fun)
        return obj

    @classmethod
    def add_class_method(self):
        pass

    def get_head_info(self):
        class HeadInfo:
            def __init__(self, blog_name, blog_description, title='邪恶二进制'):
                self.blog_name = blog_name
                self.blog_description = blog_description
                self.title = title

        blog_name = Options.objects.filter(option_name='blog_name').last()
        if blog_name is not None:
            blog_name = blog_name.option_value
        else:
            blog_name = ''

        blog_description = Options.objects.filter(option_name='blog_description').last()
        if blog_description is not None:
            blog_description = blog_description.option_value
        else:
            blog_description = ''

        info = HeadInfo(blog_name, blog_description)
        return info
