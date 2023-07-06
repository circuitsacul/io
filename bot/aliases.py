_ALIASES = {
    "python": ["py", "python3", "py3"],
    "python2": ["py2"],
    "c++": ["cpp", "cp", "c+"],
    "csharp": ["c#"],
    "rust": ["rs"],
}

ALIASES: dict[str, str] = {}
for lang, aliases in _ALIASES.items():
    for alias in aliases:
        ALIASES[alias] = lang
