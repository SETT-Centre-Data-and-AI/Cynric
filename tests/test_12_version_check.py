from cynric.support.version_check import _is_newer


def test_dev_version_ahead_of_pypi_is_not_newer() -> None:
    assert not _is_newer("1.7.8", "1.7.9.dev0")


def test_newer_release_is_detected() -> None:
    assert _is_newer("1.7.9", "1.7.8")
