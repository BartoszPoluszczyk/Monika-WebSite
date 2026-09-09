from django.template import Context, Template
from django.test import SimpleTestCase

from main.templatetags.content_formatting import accent_text


class AccentTextFilterTests(SimpleTestCase):
    def test_highlights_only_marked_fragment_and_escapes_other_html(self):
        rendered = accent_text('Zdrowie to **odŻYWIENIE**. <script>alert(1)</script>')
        self.assertIn('<span class="content-accent">odŻYWIENIE</span>', rendered)
        self.assertIn('&lt;script&gt;alert(1)&lt;/script&gt;', rendered)
        self.assertNotIn('<script>', rendered)

    def test_can_be_used_before_linebreaks_in_templates(self):
        rendered = Template(
            "{% load content_formatting %}{{ text|accent_text|linebreaks }}"
        ).render(Context({"text": "Pierwszy akapit\n\n**Drugi akapit**"}))
        self.assertIn('<span class="content-accent">Drugi akapit</span>', rendered)
