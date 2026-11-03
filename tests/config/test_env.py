from bots_place.config.env import Settings


def test_settings_load() -> None:
    assert isinstance(Settings(), Settings)
