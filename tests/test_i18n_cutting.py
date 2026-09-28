import utils.i18n_cut  # noqa: F401 — registers extra keys
from utils.i18n import set_language, t


def test_cutting_confirm_strings_en_and_fa():
    set_language("en")
    assert "inventory" in t("cut.apply_inventory").lower()
    assert "2" in t("cut.confirmed_summary", n=2)
    assert "pip install pulp" in t("cut.pulp_missing")
    assert t("err.system") == "System Error"

    set_language("fa")
    assert "موجودی" in t("cut.apply_inventory")
    assert "۲" in t("cut.confirmed_summary", n=2) or "2" in t("cut.confirmed_summary", n=2)
    assert "PuLP" in t("cut.pulp_missing")
    assert t("common.error") == "خطا"
    assert t("err.critical")


def test_missing_key_falls_back_to_key():
    set_language("en")
    assert t("does.not.exist") == "does.not.exist"
