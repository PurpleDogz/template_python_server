"""Central place to setup ThemeConfig
"""

from pydantic import BaseSettings

_config_cache = None

# Dark
BW_THEME_VAPOR = "vapor"
BW_THEME_CYBORG = "cyborg"
BW_THEME_DARKLY = "darkly"
BW_THEME_SLATE = "slate"
BW_THEME_SOLAR = "solar"

# Light
BW_THEME_SUPERHERO = "superhero"
BW_THEME_SANDSTONE = "sandstone"
BW_THEME_MATERIA = "materia"
BW_THEME_SPACELAB = "spacelab"
BW_THEME_FLATLY = "flatly"


class ThemeConfig(BaseSettings):
    # Select overall theme
    BOOTSWATCH: str = BW_THEME_SUPERHERO
    # Select the internal theme
    BOOTWATCH_PROPERTY: str = "dark"
    BOOTWATCH_PROPERTY_EX: str = "primary"

    CARD_CLASS: str = "border-" + BOOTWATCH_PROPERTY
    CHART_TOOLTIP_BG: str = "#000000"

    NAVBAR_TEXT_CLASS: str = "bg-" + BOOTWATCH_PROPERTY
    NAVBAR_CLASS: str = "navbar-dark"

    TABLE_CLASS: str = "table-" + BOOTWATCH_PROPERTY
    TABLE_ROW_CLASS: str = "table-default"

    TABLE_FONT_SIZE_EXTRA_LARGE: str = "18px"
    TABLE_FONT_SIZE_LARGE: str = "16px"
    TABLE_FONT_SIZE: str = "15px"
    TABLE_FONT_SIZE_MEDIUM: str = "14px"
    TABLE_FONT_SIZE_SMALL: str = "12px"
    TABLE_FONT_SIZE_SMALL_MOBILE: str = "11px"
    TABLE_ALT_HEADER_COLOR: str = "#58fadb"

    BADGE_PRIMARY: str = "bg-secondary"

    BUTTON_RADIO_CLASS: str = "btn-outline-" + BOOTWATCH_PROPERTY_EX

    BUTTON_CLASS: str = "btn-" + BOOTWATCH_PROPERTY

    COLOR_COMMENT: str = "var(--bs-info)"
    COLOR_GREEN: str = "#AAFF00"
    COLOR_ORANGE: str = "#FFA500"
    COLOR_YELLOW: str = "#FFFF00"
    COLOR_RED: str = "#DD4659"

    class Config:
        extra = "allow"
        env_file = ".theme"
        env_file_encoding = "utf-8"


def get() -> ThemeConfig:
    global _config_cache
    if not _config_cache:
        _config_cache = ThemeConfig()
    return _config_cache
