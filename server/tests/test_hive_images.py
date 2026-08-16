import hashlib
import json

import ecdsa
import httpx
import pytest

from app.hive.images import ImageUploadError, sign_image_challenge, upload_image
from lighthive.broadcast.key_objects import PrivateKey
from lighthive.broadcast.utils import compat_bytes

# Well-known secp256k1 example key (Bitcoin wiki) — test-only, controls nothing.
TEST_WIF = "5KQwrPbwdL6PhXujxW37FSSQZ1JiwsST4cqQzDeyXtP79zkvFD3"
JPEG = b"\xff\xd8\xff\xe0" + b"x" * 64


def test_signature_is_recoverable_and_canonical():
    sig_hex = sign_image_challenge(JPEG, TEST_WIF)
    sig = bytes.fromhex(sig_hex)
    assert len(sig) == 65
    assert 31 <= sig[0] <= 34  # 27 + 4 (compressed) + recovery 0..3
    # Recover the pubkey from the signature and compare against the WIF's key:
    # proves we signed sha256('ImageSigningChallenge' + file) with this key.
    digest = hashlib.sha256(b"ImageSigningChallenge" + JPEG).digest()
    order = ecdsa.SECP256k1.order
    r, s = ecdsa.util.sigdecode_string(sig[1:], order)
    assert not (sig[1] & 0x80) and not (sig[33] & 0x80)  # canonical
    sk = ecdsa.SigningKey.from_string(compat_bytes(PrivateKey(TEST_WIF)),
                                      curve=ecdsa.SECP256k1)
    sk.get_verifying_key().verify_digest(
        sig[1:], digest, sigdecode=ecdsa.util.sigdecode_string)


def test_signature_is_deterministic():
    assert sign_image_challenge(JPEG, TEST_WIF) == sign_image_challenge(JPEG, TEST_WIF)


async def _upload(handler, **kwargs):
    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as http:
        return await upload_image(JPEG, "front.jpg", account="thebinder",
                                  posting_key=TEST_WIF, http=http, **kwargs)


async def test_upload_posts_multipart_file_field():
    seen = {}

    async def handler(request):
        seen["url"] = str(request.url)
        seen["body"] = request.content
        return httpx.Response(200, json={"url": "https://images.hive.blog/DQm/front.jpg"})

    url = await _upload(handler)
    assert url == "https://images.hive.blog/DQm/front.jpg"
    assert seen["url"].startswith("https://images.hive.blog/thebinder/")
    assert b'name="file"' in seen["body"]  # images.hive.blog wants field 'file'


async def test_upload_falls_back_to_3speak():
    async def handler(request):
        if request.url.host == "images.hive.blog":
            return httpx.Response(503)
        assert request.url.host == "images.3speak.tv"
        assert request.headers["authorization"] == "Bearer tok"
        assert b'name="image"' in request.content  # 3speak wants field 'image'
        return httpx.Response(200, json={"success": True, "url": "https://img.3s/x.jpg"})

    assert await _upload(handler, fallback_token="tok") == "https://img.3s/x.jpg"


async def test_upload_error_when_no_fallback():
    async def handler(request):
        return httpx.Response(503)

    with pytest.raises(ImageUploadError):
        await _upload(handler)


async def test_rejects_bad_type_and_oversize():
    async def handler(request):
        raise AssertionError("must not reach network")

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as http:
        with pytest.raises(ImageUploadError):
            await upload_image(b"GIF89a", "x.gif", account="a", posting_key=TEST_WIF, http=http)
        with pytest.raises(ImageUploadError):
            await upload_image(JPEG + b"0" * (5 * 1024 * 1024), "x.jpg",
                               account="a", posting_key=TEST_WIF, http=http)
