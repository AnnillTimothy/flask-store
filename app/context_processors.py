"""
Global context processor – injects branding variables into every template
so that store identity can be changed in one place.
"""


def inject_branding():
    return {
        'store_name': 'The Bodhi Tree',
        'tagline': 'Enter the journey',
        'primary_color': '#7c3aed',
        'accent_color': '#d4a056',
    }
