from django import forms
from django.contrib.auth.forms import ReadOnlyPasswordHashField
from django.contrib.auth.models import User
from django.forms import ModelForm
from django.utils.translation import ugettext_lazy as _

from blog.models import Posts, Users, Pages


class CommentForm(forms.Form):
    comment = forms.CharField()
    author = forms.CharField()
    email = forms.EmailField()
    url = forms.URLField(required=False)

    def clean(self):
        cleaned_data = super(CommentForm, self).clean()
        tmp_email = cleaned_data.get('email')
        author = cleaned_data.get('author')
        comment = cleaned_data.get('comment')
        url = cleaned_data.get('url')

        if tmp_email is None:
            self._errors['email'] = self.error_class(['亲，邮箱给我填正确来!'])
        if author is None:
            self._errors['author'] = self.error_class(['亲，没昵称谁都不认识你!'])
        if comment is None:
            self._errors['comment'] = self.error_class(['我靠，评论不写还评论个啥？'])
        else:
            if len(comment) > 200:
                msg = '我靠，评论太长了共%d个字符，不能超过200个字符！' % len(comment)
                self._errors['comment'] = self.error_class([msg])
        if url is None:
            self._errors['url'] = self.error_class(['url没写正确啊！'])
        return cleaned_data


class PostsForm(ModelForm):
    title = forms.CharField(widget=forms.TextInput(attrs={'size': 80, }), label='标题')

    class Meta:
        model = Posts
        fields = '__all__'


class PagesForm(ModelForm):
    title = forms.CharField(widget=forms.TextInput(attrs={'size': 80, }), label='标题')

    class Meta:
        model = Pages
        fields = '__all__'


class UserCreationForm(forms.ModelForm):
    error_messages = {
        'duplicate_username': _("A user with that username already exists."),
        'password_mismatch': _("The two password fields didn't match."),
    }

    user_login = forms.RegexField(label=_("Username"), max_length=30,
                                  regex=r'^[\w.@+-]+$',
                                  help_text=_("Required. 30 characters or fewer. Letters, digits and "
                                              "@/./+/-/_ only."),
                                  error_messages={
                                      'invalid': _("This value may contain only letters, numbers and "
                                                   "@/./+/-/_ characters.")})
    user_password = forms.CharField(label=_("Password"), widget=forms.PasswordInput)

    class Meta:
        model = Users
        fields = '__all__'

        def clean_useremail(self):
            pass

    def clean_username(self):
        username = self.cleaned_data["user_login"]
        try:
            User._default_manager.get(user_login=username)
        except User.DoesNotExist:
            return username
        raise forms.ValidationError(
            self.error_messages['duplicate_username'],
            code='duplicate_username',
        )

    def clean_password2(self):
        password1 = self.cleaned_data.get("user_password")
        password2 = self.cleaned_data.get("user_password")
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError(
                self.error_messages['password_mismatch'],
                code='password_mismatch',
            )
            return password2

    def save(self, commit=True):
        user = super(UserCreationForm, self).save(commit=False)
        user.set_password(self.cleaned_data["user_password"])
        if commit:
            user.save()
        return user


class UserChangeForm(forms.ModelForm):
    user_login = forms.RegexField(
        label=_("Username"), max_length=30, regex=r"^[\w.@+-]+$",
        help_text=_("Required. 30 characters or fewer. Letters, digits and "
                    "@/./+/-/_ only."),
        error_messages={
            'invalid': _("This value may contain only letters, numbers and "
                         "@/./+/-/_ characters.")})
    user_password = ReadOnlyPasswordHashField(label=_("Password"),
                                          help_text=_("Raw passwords are not stored, so there is no way to see "
                                                      "this user's password, but you can change the password "
                                                      "using <a href=\"password/\">this form</a>."))

    class Meta:
        model = Users
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super(UserChangeForm, self).__init__(*args, **kwargs)
        f = self.fields.get('user_permissions', None)
        if f is not None:
            f.queryset = f.queryset.select_related('content_type')

    def clean_user_password(self):
        return self.initial["user_password"]
