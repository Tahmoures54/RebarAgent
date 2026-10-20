from pathlib import Path

from ui.cutting_plan_window import CuttingPlanWindow


def test_html_export_escapes_untrusted_project_and_grade_text(tmp_path, monkeypatch):
    output = tmp_path / "cutting-plan.html"
    monkeypatch.setattr(
        "ui.cutting_plan_window.filedialog.asksaveasfilename",
        lambda **kwargs: str(output),
    )
    monkeypatch.setattr("ui.cutting_plan_window.messagebox.showinfo", lambda *a, **k: None)
    monkeypatch.setattr("ui.cutting_plan_window.messagebox.showerror", lambda *a, **k: None)

    window = object.__new__(CuttingPlanWindow)
    window.plans_per_group = {
        (16.0, '<script>alert("grade")</script>'): {
            "plans": [{"bin": [(2.0, None)], "bar_length": 12.0, "scrap_id": None}]
        }
    }
    window.project_id = '<img src=x onerror="alert(1)">'
    window.plan_status = "draft"
    window.stock_len = 12.0

    window.export_html()
    exported = output.read_text(encoding="utf-8")

    assert "&lt;img src=x onerror=&quot;alert(1)&quot;&gt;" in exported
    assert "&lt;script&gt;alert(&quot;grade&quot;)&lt;/script&gt;" in exported
    assert "<script>alert(" not in exported
    assert "<img src=x" not in exported
