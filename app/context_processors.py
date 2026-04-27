"""
Global context processor – injects branding variables into every template.
Values are read from the CompanySetting DB row so the client can change them
via the admin without a redeploy.
"""


def inject_branding():
    try:
        from app.models.company_setting import CompanySetting
        settings = CompanySetting.get()
        return {
            'store_name': settings.store_name or 'The Bodhi Tree',
            'tagline': settings.tagline or 'Enter the journey',
            'primary_color': '#7c3aed',
            'accent_color': '#d4a056',
            'company': settings,
        }
    except Exception:
        return {
            'store_name': 'The Bodhi Tree',
            'tagline': 'Enter the journey',
            'primary_color': '#7c3aed',
            'accent_color': '#d4a056',
            'company': None,
        }
