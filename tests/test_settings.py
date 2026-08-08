from app.config.settings import settings

def test_settings_admin_ids():
    assert isinstance(settings.admin_ids, list)
    assert 7306854093 in settings.admin_ids
