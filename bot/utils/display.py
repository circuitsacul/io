def format_text(text: str) -> str:
    return (
        # GCC is stupid.
        text.replace("\x1b[K", "")
        # Discord doesn't understand this alias.
        .replace("\x1b[m", "\x1b[0m")
        # Discord doesn't understand this either.
        .replace("\x1b[01m", "\x1b[1m")
    )
