"""Upload card images to images.hive.blog (fallback: images.3speak.tv).

Challenge is 'ImageSigningChallenge' + raw file bytes, sha256'd and signed
with the app posting key as a recoverable compact signature — the same
scheme Hive frontends use. Uploads are PERMANENT (no delete API), so type
and size are validated before any bytes leave the server.
"""
import hashlib
import logging
import struct

import ecdsa
import httpx
from lighthive.broadcast.key_objects import PrivateKey
from lighthive.broadcast.utils import compat_bytes

logger = logging.getLogger(__name__)

CHALLENGE_PREFIX = b"ImageSigningChallenge"
MAX_IMAGE_BYTES = 5 * 1024 * 1024  # permanent CDN objects; client pre-compresses
ALLOWED_MAGIC = {
    b"\xff\xd8\xff": "image/jpeg",
    b"\x89PNG": "image/png",
    b"RIFF": "image/webp",
}


class ImageUploadError(Exception):
    """User-safe message; details are logged."""


def _is_canonical(sig: bytes) -> bool:
    return (not (sig[0] & 0x80)
            and not (sig[0] == 0 and not (sig[1] & 0x80))
            and not (sig[32] & 0x80)
            and not (sig[32] == 0 and not (sig[33] & 0x80)))


def _recovery_param(digest: bytes, signature: bytes, vk: ecdsa.VerifyingKey) -> int:
    order = ecdsa.SECP256k1.order
    curve = ecdsa.SECP256k1.curve
    generator = ecdsa.SECP256k1.generator
    r, s = ecdsa.util.sigdecode_string(signature, order)
    e = ecdsa.util.string_to_number(digest)
    for i in range(4):
        x = r + (i // 2) * order
        alpha = (pow(x, 3, curve.p()) + curve.b()) % curve.p()
        beta = ecdsa.numbertheory.square_root_mod_prime(alpha, curve.p())
        y = beta if (beta - (i % 2)) % 2 == 0 else curve.p() - beta
        R = ecdsa.ellipticcurve.Point(curve, x, y, order)
        Q = ecdsa.numbertheory.inverse_mod(r, order) * (s * R + (-e % order) * generator)
        candidate = ecdsa.VerifyingKey.from_public_point(Q, curve=ecdsa.SECP256k1)
        if candidate.to_string() == vk.to_string():
            return i
    raise ImageUploadError("Could not sign the image upload.")


def sign_image_challenge(data: bytes, posting_key_wif: str) -> str:
    digest = hashlib.sha256(CHALLENGE_PREFIX + data).digest()
    sk = ecdsa.SigningKey.from_string(compat_bytes(PrivateKey(posting_key_wif)),
                                      curve=ecdsa.SECP256k1)
    order = sk.curve.generator.order()
    attempt = 0
    while True:
        # Deterministic RFC6979 k, with a counter mixed in only when the first
        # candidate is non-canonical — signatures stay reproducible.
        k = ecdsa.rfc6979.generate_k(
            order, sk.privkey.secret_multiplier, hashlib.sha256,
            hashlib.sha256(digest + struct.pack("I", attempt)).digest())
        der = sk.sign_digest(digest, sigencode=ecdsa.util.sigencode_der, k=k)
        r, s = ecdsa.util.sigdecode_der(der, order)
        signature = ecdsa.util.sigencode_string(r, s, order)
        len_r, len_s = der[3], der[5 + der[3]]
        if len_r == 32 and len_s == 32 and _is_canonical(signature):
            break
        attempt += 1
    i = _recovery_param(digest, signature, sk.get_verifying_key()) + 4 + 27
    return (struct.pack("<B", i) + signature).hex()


def _validate(data: bytes) -> None:
    if len(data) > MAX_IMAGE_BYTES:
        raise ImageUploadError("Image too large to publish (5MB max).")
    if not any(data.startswith(magic) for magic in ALLOWED_MAGIC):
        raise ImageUploadError("Only JPEG, PNG, or WebP images can be published.")


async def upload_image(data: bytes, filename: str, *, account: str, posting_key: str,
                       http: httpx.AsyncClient, fallback_token: str = "") -> str:
    _validate(data)
    signature = sign_image_challenge(data, posting_key)
    try:
        resp = await http.post(f"https://images.hive.blog/{account}/{signature}",
                               files={"file": (filename, data)})
        if resp.status_code == 200 and resp.json().get("url"):
            return resp.json()["url"]
        logger.warning("images.hive.blog upload failed: %s", resp.status_code)
    except httpx.TransportError as exc:
        logger.warning("images.hive.blog unreachable: %s", exc)

    if fallback_token:
        try:
            resp = await http.post("https://images.3speak.tv/upload",
                                   headers={"Authorization": f"Bearer {fallback_token}"},
                                   files={"image": (filename, data)})
            body = resp.json() if resp.status_code == 200 else {}
            if body.get("url"):
                return body["url"]
            logger.warning("3speak fallback failed: %s", resp.status_code)
        except httpx.TransportError as exc:
            logger.warning("3speak unreachable: %s", exc)
    raise ImageUploadError("Image hosting is unavailable right now. Try again later.")
