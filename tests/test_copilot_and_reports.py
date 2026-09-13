from logic.agent_brain import AgentBrain, analyze_project
from logic.cutting_coach import coach_from_plan_groups
from utils.envfile import load_env_file
from utils.report_brand import footer_html, copilot_strip_html


def test_envfile_parses_and_skips_comments(tmp_path, monkeypatch):
    path = tmp_path / ".env"
    path.write_text("# c\nREBARAGENT_PRICE_PRO_1Y_USD=111\nEMPTY=\n", encoding="utf-8")
    monkeypatch.delenv("REBARAGENT_PRICE_PRO_1Y_USD", raising=False)
    n = load_env_file(str(path), override=True)
    assert n >= 1
    import os
    assert os.environ["REBARAGENT_PRICE_PRO_1Y_USD"] == "111"


def test_agent_brain_empty_project(isolated_db):
    from db.models import ProjectModel
    pid = ProjectModel.create("t", "c")
    rep = analyze_project(pid)
    assert 0 <= rep.health_score <= 100
    assert rep.actions
    brain = AgentBrain(pid)
    assert brain.health_score() == float(rep.health_score)


def test_cutting_coach_flags_short_pieces_on_12m():
    groups = {
        (12.0, "A3"): {
            "plans": [
                {"bar_length": 12.0, "bin": [(2.0, {}), (2.0, {}), (1.5, {})]},
            ]
        }
    }
    tips = coach_from_plan_groups(groups, 12.0, lang="en")
    assert tips
    assert any("6 m" in t or "6m" in t or "Utilization" in t for t in tips)


def test_report_footer_advertises_rebaragent():
    html = footer_html("en")
    assert "RebarAgent" in html
    assert "ad-footer" in html
    assert "WhatsApp" in html
    strip = copilot_strip_html(82, "Run cutting plan")
    assert "82" in strip
    assert "Copilot" in strip
