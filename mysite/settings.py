# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
import os

# BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE_DIR = os.path.dirname(os.path.dirname(__file__))

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.7/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'tu^5doh&bqq4e00&@q0z(d$lwb_bqjc7c6#w=eht3vziqakm!k'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['*', '127.0.0.1', '.evilbinary.org', 'localhost']

# Application definition
INSTALLED_APPS = (
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'blog',
    'ckeditor',
    'ckeditor_uploader',
)

MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
)

ROOT_URLCONF = 'mysite.urls'

WSGI_APPLICATION = 'mysite.wsgi.application'

MEDIA_DIR = BASE_DIR
DATABASE_DIR = BASE_DIR

# OpenShift define here


if os.environ.has_key('OPENSHIFT_REPO_DIR'):
    DEBUG = bool(os.environ.get('DEBUG', False))
    if DEBUG:
        print("WARNING: The DEBUG environment is set to True.")
    TEMPLATE_DEBUG = DEBUG
    MEDIA_DIR = os.path.join(os.environ['OPENSHIFT_DATA_DIR'])
    DATABASE_DIR = os.path.join(os.environ['OPENSHIFT_DATA_DIR'])

# Database
# https://docs.djangoproject.com/en/1.7/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'dushu',
        'USER': 'root',
        'PASSWORD': '7u8i9o0p',
        'HOST': '127.0.0.1',
        'PORT': '3306'
    }
}

# Internationalization
# https://docs.djangoproject.com/en/1.7/topics/i18n/

# LANGUAGE_CODE = 'en-us'
LANGUAGE_CODE = 'zh-Hans'

TIME_ZONE = 'Asia/Shanghai'
USE_TZ = False

# TIME_FORMAT = 'a'
DATETIME_FORMAT = 'Y/m/d H:i:s'

USE_I18N = True

USE_L10N = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.7/howto/static-files/

STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'static')

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(os.path.dirname(__file__), '../blog/templates').replace('\\', '/')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                "django.contrib.auth.context_processors.auth",
                "django.template.context_processors.debug",
                "django.template.context_processors.i18n",
                "django.template.context_processors.media",
                "django.template.context_processors.static",
                "django.template.context_processors.tz",
                "django.contrib.messages.context_processors.messages",
                "django.template.context_processors.request",
            ]
        }
    }
]

STATICFILES_FINDERS = (
    "django.contrib.staticfiles.finders.AppDirectoriesFinder",
    "django.contrib.staticfiles.finders.FileSystemFinder",
)

MYBLOG_PATH = os.path.join(os.path.dirname(__file__), '../blog/').replace('\\', '/')

STATICFILES_DIRS = (
    ('css', os.path.join(STATIC_ROOT, 'css')),
    ('js', os.path.join(STATIC_ROOT, 'js')),
    ('img', os.path.join(STATIC_ROOT, 'img')),
    ('admin/css', os.path.join(STATIC_ROOT, 'admin/css')),
    ('admin/js', os.path.join(STATIC_ROOT, 'admin/js')),
    ('admin/js/admin', os.path.join(STATIC_ROOT, 'admin/js/admin')),
    ('admin/img', os.path.join(STATIC_ROOT, 'admin/img')),
)

# 头像地址
GRAVATAR_URL_PREFIX = 'https://secure.gravatar.com/avatar/'

MEDIA_URL = "/media/"
MEDIA_ROOT = os.path.join(MEDIA_DIR, "media")
CKEDITOR_UPLOAD_PATH = os.path.join(MEDIA_ROOT, 'uploads')

CKEDITOR_CONFIGS = {
    'default': {
        'toolbar': [
            ['Source', '-', 'Save', 'PasteText', 'Undo', 'Redo', 'RemoveFormat'],
            ['Bold', 'Italic', 'Underline', 'Strike', '-', 'Subscript', 'Superscript'],
            ['NumberedList', 'BulletedList', 'JustifyLeft', 'JustifyCenter', 'JustifyRight', 'JustifyBlock'],
            ['Image', 'Maximize', 'ShowBlocks']
        ],
        'width': 800,
        'height': 350,
        'toolbarCanCollapse': False,
    },
}

AUTH_USER_MODEL = "blog.Users"

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'django.db.backends': {
            'handlers': ['console'],
            'propagate': True,
            'level': 'DEBUG',
        },
    }
}
