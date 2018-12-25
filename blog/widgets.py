from itertools import *

from ckeditor.widgets import CKEditorWidget
from django.forms.widgets import *
from django.utils.encoding import force_unicode
from django.utils.html import *

from blog.models import Link
from widgets import *


class TreeSelect(Select):
    def __init__(self, attrs=None):
        super(Select, self).__init__(attrs)

    def render_option(self, selected_choices, option_value, option_label):
        option_value = force_unicode(option_value)
        if option_value in selected_choices:
            selected_html = u' selected="selected"'
            if not self.allow_multiple_selected:
                selected_choices.remove(option_value)
        else:
            selected_html = ''
        return u'<option value="%s"%s>%s</option>' % (
            escape(option_value), selected_html,
            conditional_escape(force_unicode(option_label)).replace(' ', ' '))

    def render_options(self, choices, selected_choices):
        ch = [()]
        print ch[0]
        self.choices = ch[0]
        selected_choices = set(force_unicode(v) for v in selected_choices)
        output = []
        output.append('<optgroup label="aaaa">aaaa</optgroup>')
        output.append('<optgroup label="bbbbbbbbb">aaaa</optgroup>')

        for option_value, option_label in chain(self.choices, choices):
            if isinstance(option_label, (list, tuple)):
                output.append(u'<optgroup label="%s">' % escape(force_unicode(option_value)).replace(' ', ' '))
                for option in option_label:
                    output.append(self.render_option(selected_choices, *option))
                output.append(u'</optgroup>')
            else:
                output.append(self.render_option(selected_choices, option_value, option_label))
        return u'\n'.join(output)


class MySelect(Select):
    def __init__(self, attrs=None):
        super(Select, self).__init__(attrs)

    def render(self, name, value, attrs=None, choices=()):
        # TODO: choices
        return super(MySelect, self).render(name, value, attrs)

    def render_option(self, selected_choices, option_value, option_label):
        if option_value in selected_choices:
            selected_html = u' selected="selected"'
            if not self.allow_multiple_selected:
                selected_choices.remove(option_value)
        else:
            selected_html = ''

        return u'<option value="%s"%s>%s</option>' % (
            escape(option_value), selected_html,
            conditional_escape(force_unicode(option_label)).replace(' ', ' '))

    def render_options(self, choices, selected_choices):
        ret = []
        vals = []
        for option_value, option_label in chain(self.choices, choices):
            if option_value != '':
                vals.append(int(option_value))

        links = Link.objects.filter(link_id__in=vals)
        dic = {l.link_id: l for l in links}
        for option_value, option_label in chain(self.choices, choices):
            if option_value in dic:
                option_label = dic[option_value]
            ret.append(self.render_option(selected_choices, option_value, option_label))

        return ''.join(ret)


class RichTextEditorWidget(CKEditorWidget):
    pass
