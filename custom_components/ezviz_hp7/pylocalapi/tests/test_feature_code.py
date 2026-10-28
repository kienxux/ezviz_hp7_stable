"""Tests for the persistent EZVIZ featureCode (terminal id).

Run with:  python -m pytest tests/test_feature_code.py
Only the standard library is needed; the module is loaded by path so Home
Assistant does not have to be installed.
"""

from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path
import re

import pytest

SRC = (
    Path(__file__).resolve().parents[1]
    / "custom_components"
    / "ezviz_hp7"
    / "pylocalapi"
    / "constants.py"
)
HEX32 = re.compile(r"[0-9a-f]{32}")


@pytest.fixture(scope="module")
def mod():
    # Importing the module computes FEATURE_CODE; force it so the import itself
    # never writes into the repository checkout.
    os.environ["EZVIZ_HP7_FEATURE_CODE"] = "b" * 32
    try:
        spec = importlib.util.spec_from_file_location("ezviz_constants_under_test", SRC)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
    finally:
        del os.environ["EZVIZ_HP7_FEATURE_CODE"]
    return module


def make_layout(tmp_path: Path) -> tuple[Path, Path]:
    """Create <config>/custom_components/ezviz_hp7/pylocalapi/constants.py."""

    config = tmp_path / "config"
    pkg = config / "custom_components" / "ezviz_hp7" / "pylocalapi"
    pkg.mkdir(parents=True)
    fake = pkg / "constants.py"
    fake.write_text("# placeholder\n")
    return config, fake


def test_generates_and_persists(mod, tmp_path):
    config, fake = make_layout(tmp_path)
    first = mod._resolve_feature_code(fake, environ={})
    assert HEX32.fullmatch(first)
    stored = config / ".storage" / mod.FEATURE_CODE_FILENAME
    assert stored.read_text().strip() == first
    # a "restart" returns the same value
    assert mod._resolve_feature_code(fake, environ={}) == first


def test_stable_when_mac_changes(mod, tmp_path, monkeypatch):
    """The whole point: a different MAC/IP must not change the code."""

    _, fake = make_layout(tmp_path)
    first = mod._resolve_feature_code(fake, environ={})
    monkeypatch.setattr(mod.uuid, "getnode", lambda: 0x0242AC110099)
    assert mod._resolve_feature_code(fake, environ={}) == first


def test_environment_override_wins(mod, tmp_path):
    _, fake = make_layout(tmp_path)
    forced = "a" * 32
    assert mod._resolve_feature_code(fake, environ={"EZVIZ_HP7_FEATURE_CODE": forced.upper()}) == forced
    # invalid override is ignored
    assert HEX32.fullmatch(
        mod._resolve_feature_code(fake, environ={"EZVIZ_HP7_FEATURE_CODE": "nothex"})
    )


def test_adopts_code_from_existing_config_entry(mod, tmp_path):
    config, fake = make_layout(tmp_path)
    existing = "0123456789abcdef0123456789abcdef"
    storage = config / ".storage"
    storage.mkdir()
    (storage / "core.config_entries").write_text(
        json.dumps(
            {
                "data": {
                    "entries": [
                        {"domain": "other", "data": {"token": {"feature_code": "f" * 32}}},
                        {"domain": "ezviz_hp7", "data": {"token": {"feature_code": existing}}},
                    ]
                }
            }
        )
    )
    assert mod._resolve_feature_code(fake, environ={}) == existing
    assert (storage / mod.FEATURE_CODE_FILENAME).read_text().strip() == existing


@pytest.mark.parametrize(
    "content",
    ["not json", json.dumps({}), json.dumps({"data": {"entries": [{"domain": "ezviz_hp7"}]}})],
)
def test_bad_config_entries_file_is_ignored(mod, tmp_path, content):
    config, fake = make_layout(tmp_path)
    (config / ".storage").mkdir()
    (config / ".storage" / "core.config_entries").write_text(content)
    assert HEX32.fullmatch(mod._resolve_feature_code(fake, environ={}))


def test_corrupt_code_file_is_replaced(mod, tmp_path):
    config, fake = make_layout(tmp_path)
    stored = config / ".storage" / mod.FEATURE_CODE_FILENAME
    stored.parent.mkdir()
    stored.write_text("garbage")
    code = mod._resolve_feature_code(fake, environ={})
    assert HEX32.fullmatch(code)
    assert stored.read_text().strip() == code


def test_falls_back_to_package_dir_when_storage_not_writable(mod, tmp_path):
    config, fake = make_layout(tmp_path)
    # .storage exists as a *file* -> cannot be used as a directory
    (config / ".storage").write_text("block")
    code = mod._resolve_feature_code(fake, environ={})
    assert HEX32.fullmatch(code)
    assert (fake.parent / f".{mod.FEATURE_CODE_FILENAME}").read_text().strip() == code
    assert mod._resolve_feature_code(fake, environ={}) == code


def test_nonstandard_layout_uses_package_dir(mod, tmp_path):
    fake = tmp_path / "somewhere" / "constants.py"
    fake.parent.mkdir()
    fake.write_text("# placeholder\n")
    code = mod._resolve_feature_code(fake, environ={})
    assert (fake.parent / f".{mod.FEATURE_CODE_FILENAME}").read_text().strip() == code


def test_legacy_fallback_when_nothing_writable(mod, tmp_path, monkeypatch):
    _, fake = make_layout(tmp_path)
    monkeypatch.setattr(mod, "_write_code", lambda path, code: False)
    monkeypatch.setattr(mod.uuid, "getnode", lambda: 0x0242AC110002)
    code = mod._resolve_feature_code(fake, environ={})
    mac = ":".join(f"{(0x0242AC110002 >> i) & 0xFF:02x}" for i in range(40, -1, -8))
    assert code == mod.md5(mac.encode()).hexdigest()


def test_module_level_constants_are_consistent(mod):
    assert mod.FEATURE_CODE == "b" * 32
    assert mod.REQUEST_HEADER["featureCode"] == mod.FEATURE_CODE
