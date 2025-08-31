import bleach
import io, base64, secrets, string, random, hashlib, logging
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from django.core.cache import cache

log = logging.getLogger("captcha")

ABC = string.ascii_letters + string.digits
H = lambda s: hashlib.sha256(s.encode('utf-8')).hexdigest()

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

def _rand_code(n=5):
    return ''.join(random.choice(ABC) for _ in range(n))

def make_captcha(ttl=300):
    code = _rand_code(5)
    key  = secrets.token_urlsafe(16)
    cache.set(f'captcha:{key}', H(code.lower()), ttl)

    img = Image.new('RGB', (120, 40), '#f3f4f6')
    d = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype('DejaVuSans.ttf', 24)
    except Exception:
        font = ImageFont.load_default()
    d.text((12, 8), code, fill='#111', font=font)
    img = img.filter(ImageFilter.SMOOTH)

    buf = io.BytesIO(); img.save(buf, format='PNG', optimize=True)
    b64 = 'data:image/png;base64,' + base64.b64encode(buf.getvalue()).decode('ascii')
    return key, b64

def verify_captcha(key: str | None, code: str | None) -> bool:
    if not key or not code:
        return False
    raw  = code.strip()
    low  = raw.lower()
    stored = cache.get(f'captcha:{key}')
    cache.delete(f'captcha:{key}')
    if not stored:
        return False
    return stored in (H(low), H(raw), low, raw)