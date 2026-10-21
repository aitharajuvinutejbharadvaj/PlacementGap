from ontology.canonicalizer import CanonicalMatch, canonicalize


def canonicalize_skill(text: str, context: str | None = None) -> CanonicalMatch:
    return canonicalize(text, context)
