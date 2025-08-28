import bleach

ALLOWED_TAGS = ["a", "code", "i", "strong"]
ALLOWED_ATTRS = {"a": ["href", "title"]}
ALLOWED_PROTOCOLS = ["http", "https", "mailto"]

CLEANER = bleach.Cleaner(
    tags=ALLOWED_TAGS,
    attributes=ALLOWED_ATTRS,
    protocols=ALLOWED_PROTOCOLS,
    strip=True,
    strip_comments=True,
)

def sanitize_comment_html(raw: str) -> str:
    """
        Sanitize user-submitted comment text and auto-link bare URLs/emails.

        Pipeline:
          1) Convert plain URLs and email addresses into <a>…</a> links
             using bleach.linkify(parse_email=True).
          2) Clean the HTML with a strict allow-list to prevent XSS:
             - Allowed tags: <a>, <code>, <i>, <strong>
             - Allowed attributes:
                 * <a>: href, title
             - Allowed URL schemes: http, https, mailto
             - HTML comments and all other tags/attributes are stripped.

        The output is normalized/well-formed HTML. If input is empty, returns "".

        Args:
            raw: Raw comment text that may contain HTML.

        Returns:
            Safe HTML string containing only the allowed tags and attributes.
    """

    if not raw:
        return ""

    linked = bleach.linkify(raw, parse_email=True)

    safe_html = CLEANER.clean(linked)
    return safe_html