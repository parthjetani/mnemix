import re
import zipfile

_EMAIL_RE = re.compile(r'[\w.+-]+@[\w-]+\.\w+')
_PHONE_RE = re.compile(r'(\+?\d[\d\s\-().]{7,}\d)')
_URL_RE = re.compile(r'https?://\S+|www\.\S+')
_LINKEDIN_RE = re.compile(r'linkedin\.com/\S+', re.IGNORECASE)


def anonymize(text: str) -> str:
    text = _EMAIL_RE.sub("[EMAIL]", text)
    text = _PHONE_RE.sub("[PHONE]", text)
    text = _LINKEDIN_RE.sub("[LINKEDIN]", text)
    text = _URL_RE.sub("[URL]", text)
    return text


def escape_braces(text: str) -> str:
    return text.replace("{", "{{").replace("}", "}}")


MAX_ZIP_UNCOMPRESSED_BYTES = 500 * 1024 * 1024


def check_zip_size(zf: zipfile.ZipFile, limit: int = MAX_ZIP_UNCOMPRESSED_BYTES) -> None:
    total = sum(info.file_size for info in zf.infolist())
    if total > limit:
        raise ValueError(
            f"ZIP uncompressed size {total} bytes exceeds limit of {limit} bytes "
            f"(potential zip bomb)"
        )
