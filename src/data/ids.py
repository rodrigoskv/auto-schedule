import re
import unicodedata


def slugify(value: str) -> str:
    normalized = unicodedata.normalize("NFD", value)
    without_marks = "".join(ch for ch in normalized if unicodedata.category(ch) != "Mn")
    slug = re.sub(r"[^a-z0-9]+", "_", without_marks.lower()).strip("_")
    return slug or "item"


def unique_id(base: str, taken: set[str]) -> str:
    candidate = slugify(base)
    n = 2
    while candidate in taken:
        candidate = f"{slugify(base)}_{n}"
        n += 1
    taken.add(candidate)
    return candidate