from pathlib import Path

from streamlit.testing.v1 import AppTest


REPO_ROOT = Path(__file__).resolve().parents[1]
APP_PATH = REPO_ROOT / "app.py"
ENTRYPOINT_PATH = REPO_ROOT / "Prime_Lab.py"
APP_SOURCE = APP_PATH.read_text(encoding="utf-8")
ENTRYPOINT_SOURCE = ENTRYPOINT_PATH.read_text(encoding="utf-8")


def test_baseline_lab_uses_committed_experiment_form():
    assert 'with st.form("prime_lab_experiment_form"' in APP_SOURCE
    assert '"Apply experiment"' in APP_SOURCE
    assert 'st.session_state["prime_lab_experiment"]' in APP_SOURCE


def test_baseline_lab_entrypoint_executes_page_on_every_rerun():
    assert "from app import *" not in ENTRYPOINT_SOURCE
    assert "runpy.run_path" in ENTRYPOINT_SOURCE


def test_baseline_lab_does_not_use_legacy_sieve_animation():
    assert "build_sieve_animation" not in APP_SOURCE


def test_baseline_lab_keys_visualization_to_committed_state():
    assert "experiment_token" in APP_SOURCE
    assert "prime_lab_chart_" in APP_SOURCE
    assert "uirevision=chart_key" in APP_SOURCE


def test_baseline_lab_includes_exact_inspection_and_exports():
    assert "Inspect one integer" in APP_SOURCE
    assert '"Download state CSV"' in APP_SOURCE
    assert '"Download filter CSV"' in APP_SOURCE


def test_baseline_lab_survives_applying_a_new_range_through_real_entrypoint():
    app = AppTest.from_file(ENTRYPOINT_PATH)
    app.run(timeout=15)

    assert not app.exception
    assert app.number_input[0].label == "Range start"
    assert app.number_input[1].label == "Range end"
    assert app.button[0].label == "Apply experiment"

    app.number_input[1].set_value(750)
    app.button[0].click().run(timeout=15)

    assert not app.exception
    assert app.session_state["prime_lab_experiment"]["end"] == 750
    assert any(
        metric.label == "Prime candidates" and metric.value == "749"
        for metric in app.metric
    )
