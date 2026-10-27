import re, hashlib

def chunk_text(text, chunk_size=1800, overlap=300):
    text = re.sub(r"\n{3,}", "\n\n", text).strip()
    result, start = [], 0
    while start < len(text):
        end = min(start + chunk_size, len(text))
        if end < len(text):
            boundary = max(text.rfind("\n", start, end), text.rfind(". ", start, end), text.rfind(" ", start, end))
            if boundary > start + chunk_size // 2: end = boundary + 1
        part = text[start:end].strip()
        if part: result.append(part)
        if end == len(text): break
        start = max(start + 1, end - overlap)
    return result

def digest(text): return hashlib.sha256(text.encode("utf-8")).hexdigest()
