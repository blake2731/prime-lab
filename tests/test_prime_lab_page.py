from pathlib import Path


APP_SOURCE = Path("app.py").read_text(encoding="utf-8")


def test_baseline_lab_uses_committed_experiment_form():
    assert 'with st.form("prime_lab_experiment_form"' in APP_SOURCE
    assert '"Apply experiment"' in APP_SOURCE
    assert 'st.session_state["prime_lab_experiment"]' in APP_SOURCE


def test_baseline_lab_does_not_use_legacy_sieve_animation():
    assert "build_sieve_animation" not in APP_SOURCE


def test_baseline_lab_keys_visualization_to_committed_state():
    assert "experiment_token" in APP_SOURCE
    assert "prime_lab_chart_" in APP_SOURCE
    assert "uirevision=chart_key" in APP_SOURCE


def test_baseline_lab_includes_exact_inspection_and_exports():
    assert '"Inspect one integer"' in APP_SOURCE
    assert '"Download state CSV"' in APP_SOURCE
    assert '"Download filter CSV"' in APP_SOURCE
