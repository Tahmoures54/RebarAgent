"""Security regression tests for the Ed25519 activation-key format."""

import base64
import json

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from utils import license as license_module


def _issuer(monkeypatch, tmp_path):
    private_key = Ed25519PrivateKey.generate()
    private_path = tmp_path / "issuer.pem"
    private_path.write_bytes(
        private_key.private_bytes(
            serialization.Encoding.PEM,
            serialization.PrivateFormat.PKCS8,
            serialization.NoEncryption(),
        )
    )
    public_pem = private_key.public_key().public_bytes(
        serialization.Encoding.PEM,
        serialization.PublicFormat.SubjectPublicKeyInfo,
    )
    monkeypatch.setenv("REBARAGENT_LICENSE_PRIVATE_KEY", str(private_path))
    monkeypatch.setattr(license_module, "LICENSE_PUBLIC_KEY_PEM", public_pem)


def _license_store(monkeypatch, tmp_path):
    monkeypatch.setattr(license_module, "HIDDEN_DIR", str(tmp_path))
    monkeypatch.setattr(license_module, "HIDDEN_FILE", str(tmp_path / "license.dat"))
    monkeypatch.setattr(license_module, "get_machine_id", lambda: "mac-test")


def test_ed25519_key_activates_for_matching_machine(isolated_db, tmp_path, monkeypatch):
    _issuer(monkeypatch, tmp_path)
    _license_store(monkeypatch, tmp_path)
    key = license_module.generate_activation_key("mac-test", "1year")
    assert key.startswith("v2.")
    ok, message = license_module.activate_license(key, isolated_db)
    assert ok, message
    assert license_module.get_license_info(isolated_db)["type"] == "1year"


def test_legacy_hmac_key_is_rejected(isolated_db, tmp_path, monkeypatch):
    _license_store(monkeypatch, tmp_path)
    legacy = base64.urlsafe_b64encode(
        b"mac-test|1year|2099-12-31|2026-01-01|deadbeef"
    ).decode("ascii")
    ok, message = license_module.activate_license(legacy, isolated_db)
    assert not ok
    assert "version" in message.lower()


def test_tampered_payload_is_rejected(isolated_db, tmp_path, monkeypatch):
    _issuer(monkeypatch, tmp_path)
    _license_store(monkeypatch, tmp_path)
    key = license_module.generate_activation_key("mac-test", "1year")
    envelope = json.loads(base64.urlsafe_b64decode(key[3:] + "==").decode("utf-8"))
    envelope["payload"]["license_type"] = "unlimited"
    tampered = "v2." + base64.urlsafe_b64encode(
        json.dumps(envelope, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).decode("ascii").rstrip("=")
    ok, _ = license_module.activate_license(tampered, isolated_db)
    assert not ok


def test_issuer_fails_closed_without_private_key(monkeypatch, tmp_path):
    monkeypatch.delenv("REBARAGENT_LICENSE_PRIVATE_KEY", raising=False)
    monkeypatch.setattr(license_module, "HIDDEN_DIR", str(tmp_path))
    monkeypatch.setattr(license_module, "HIDDEN_FILE", str(tmp_path / "license.dat"))
    try:
        license_module.generate_activation_key("mac-test", "1year")
    except RuntimeError as exc:
        assert "issuance is disabled" in str(exc).lower()
    else:
        raise AssertionError("issuer unexpectedly generated a key without its private key")
