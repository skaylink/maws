from rubber_duck import __app_name__, __version__


class TestAppConstants:

    def test_app_name_is_string(self):
        assert isinstance(__app_name__, str)

    def test_version_is_string(self):
        assert isinstance(__version__, str)

    def test_app_name_not_empty(self):
        assert len(__app_name__) > 0

    def test_version_not_empty(self):
        assert len(__version__) > 0

    def test_version_format(self):
        version_parts = __version__.split(".")
        assert len(version_parts) == 3
        for part in version_parts:
            assert part.isdigit()
