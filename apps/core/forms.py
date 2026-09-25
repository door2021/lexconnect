from django.forms.renderers import TemplatesSetting


class FormRenderer(TemplatesSetting):
    """Render every form field through our Tailwind-styled field template."""

    field_template_name = "forms/field.html"
