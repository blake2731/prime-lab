from pathlib import Path

from streamlit.testing.v1 import AppTest


REPO_ROOT = Path(__file__).resolve().parents[1]
APP_PATH = REPO_ROOT / "app.py"
ENTRYPOINT_PATH = REPO_ROOT / "Prime_Lab.py"
THEME_PATH = REPO_ROOT / ".streamlit" / "config.toml"
ANIMATION_PATH = REPO_ROOT / "ui" / "sieve_animation.py"
APP_SOURCE = APP_PATH.read_text(encoding="utf-8")
ENTRYPOINT_SOURCE = ENTRYPOINT_PATH.read_text(encoding="utf-8")
THEME_SOURCE = THEME_PATH.read_text(encoding="utf-8")
ANIMATION_SOURCE = ANIMATION_PATH.read_text(encoding="utf-8")


def test_baseline_lab_uses_committed_experiment_form():
    assert 'with st.form("prime_lab_experiment_form"' in APP_SOURCE
    assert '"Apply experiment"' in APP_SOURCE
    assert 'st.session_state["prime_lab_experiment"]' in APP_SOURCE


def test_baseline_lab_entrypoint_executes_page_on_every_rerun():
    assert "from app import *" not in ENTRYPOINT_SOURCE
    assert "runpy.run_path" in ENTRYPOINT_SOURCE


def test_baseline_lab_includes_filter_playback_with_bounded_payload():
    assert "build_sieve_animation" in APP_SOURCE
    assert '"Sieve playback"' in APP_SOURCE
    assert "MAX_PLAYBACK_INTEGERS = 1_500" in APP_SOURCE
    assert "▶ Play cascade" in ANIMATION_SOURCE
    assert "prime_{prime}_focus" in ANIMATION_SOURCE
    assert "prime_{prime}_cascade_" in ANIMATION_SOURCE
    assert "prime_{prime}_settle" in ANIMATION_SOURCE
    assert "Reduced motion" in ANIMATION_SOURCE


def test_baseline_lab_keys_visualization_to_committed_state():
    assert "experiment_token" in APP_SOURCE
    assert "prime_lab_chart_" in APP_SOURCE
    assert "uirevision=chart_key" in APP_SOURCE
    assert "prime_lab_playback_" in APP_SOURCE


def test_baseline_lab_includes_exact_inspection_and_exports():
    assert "Inspect one integer" in APP_SOURCE
    assert '"Download state CSV"' in APP_SOURCE
    assert '"Download filter CSV"' in APP_SOURCE


def test_project_theme_separates_body_heading_and_code_typography():
    assert 'font = "sans-serif"' in THEME_SOURCE
    assert 'headingFont = "serif"' in THEME_SOURCE
    assert 'codeFont = "monospace"' in THEME_SOURCE
    assert "headingFontSizes" in THEME_SOURCE
    assert "headingFontWeights" in THEME_SOURCE


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
