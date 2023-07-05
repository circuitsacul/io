import re

JAVA_PUBLIC_CLASS_REGEX = re.compile(r"public\s+class")
RUST_FN_REGEX = re.compile(r"fn\s+main\s*\(\s*\)")

ZIG_STD_REGEX = re.compile(r"std\s*=")
ZIG_MAIN_FN_REGEX = re.compile(r"fn\s+main\s*\(\s*\)")


def transform_code(lang: str, code: str) -> str:
    """
    Converts the code into new code based on the language and some rules.
    """

    match lang:
        case "java":
            return JAVA_PUBLIC_CLASS_REGEX.sub("class", code, count=1)

        case "rust":
            if not RUST_FN_REGEX.search(code):
                return "fn main() {\n" f"{code}\n" "}"
            return code

        case "zig":
            if not ZIG_STD_REGEX.search(code):
                header = 'const std = @import("std");'
            else:
                header = ""

            if not ZIG_MAIN_FN_REGEX.search(code):
                return f"{header}\n" "pub fn main() !void { " f"{code}" "}"

            return f"{header}\n{code}"

        case _:
            return code
