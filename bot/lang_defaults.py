RUN_DEFAULTS = {
    "python": "piston",
    "rust": {"amd64": "rust"},
    "go": {"amd64": "none"},
    "typescript": "piston",
    "c": {
        "amd64": {
            "clang-intel": "16.0.0",
            "clang": "16.0.0",
        },
        "aarch64": {"clang": "16.0.0"},
    },
    "c++": {
        "amd64": {
            "clang-intel": "16.0.0",
            "clang": "16.0.0",
        },
        "aarch64": {
            "clang": "16.0.0",
        },
    },
}

ASM_DEFAULTS = {
    "python": {"python": "python"},
    "rust": {"amd64": "rust"},
    "go": {"amd64": "none"},
    "typescript": "piston",
    "c": {
        "amd64": {
            "clang-intel": "16.0.0",
            "clang": "16.0.0",
        },
        "aarch64": {"clang": "16.0.0"},
    },
    "c++": {
        "amd64": {
            "clang-intel": "16.0.0",
            "clang": "16.0.0",
        },
        "aarch64": {
            "clang": "16.0.0",
        },
    },
}
