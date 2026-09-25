class HandleConverter:
    """Matches @handles in URLs; case is normalized by the view."""

    regex = r"[A-Za-z0-9_]{3,30}"

    def to_python(self, value: str) -> str:
        return value

    def to_url(self, value: str) -> str:
        return value
