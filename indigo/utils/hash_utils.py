from hashlib import md5


def generate_uuid(identifier: str) -> str:
    return md5(identifier.encode(encoding="utf8")).hexdigest()
