"""Qt-Material theme helper.

Provides `apply_theme(app)` which applies a customised dark palette while
keeping Qt-Material as the base.
"""
from qt_material import apply_stylesheet

EXTRA = {
    # Typography
    "font_family": "'Fira Code', monospace",

    # Core colours
    "primaryColor": "#ff53ff",    # neon magenta
    "accentColor": "#00d5ff",     # electric cyan
    "textColor": "#e6e6e6",
    "secondaryTextColor": "#e6e6e6",
    "backgroundColor": "#1b1d2b",  # deep navy
    "disabledTextColor": "#60738e",
    "errorColor": "#ed1d24",      # synth red

    # Component styling
    "borderRadius": "8px",
    "density_scale": "-1",  # slightly denser widgets
}


def apply_theme(app):
    """Apply customised dark palette to the given QApplication instance."""
    apply_stylesheet(app, theme="dark_teal.xml", extra=EXTRA)
