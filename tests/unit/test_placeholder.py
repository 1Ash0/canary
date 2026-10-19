"""Placeholder — ensures pytest finds something and exits 0.

Replace with real tests as each module is built (U0 onwards).
"""


def test_version() -> None:
    from ctxcheck import __version__

    assert isinstance(__version__, str)
    assert len(__version__) > 0
