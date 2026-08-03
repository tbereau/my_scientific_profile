from difflib import SequenceMatcher

__all__ = ["title_key", "title_similarity", "titles_match", "SAME_TITLE_SIMILARITY"]

# Titles of one work differ in spelling between preprint and published version
# ("parameterization" against "parametrization", scoring 0.99), while distinct
# works on a single author's record sit far below: the closest pair measured
# 0.81. The threshold goes between the two.
SAME_TITLE_SIMILARITY = 0.95


def title_key(title: str) -> str:
    """Normalise a title for comparison, dropping case and punctuation."""
    stripped = "".join(
        c if c.isalnum() or c.isspace() else " " for c in (title or "").lower()
    )
    return " ".join(stripped.split())


def title_similarity(left: str, right: str) -> float:
    return SequenceMatcher(None, title_key(left), title_key(right)).ratio()


def titles_match(left: str, right: str) -> bool:
    return title_similarity(left, right) >= SAME_TITLE_SIMILARITY
