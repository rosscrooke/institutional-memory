from dashboard.core import AttributionLog


def test_records_who_ran_a_session_and_survives_reload(tmp_path):
    path = tmp_path / "sessions.json"
    AttributionLog(path).record("sesn_1", "Alice", "expert")

    assert AttributionLog(path).who("sesn_1") == "Alice (expert)"


def test_unknown_or_missing_session_is_labelled_agent(tmp_path):
    log = AttributionLog(tmp_path / "sessions.json")

    assert log.who("sesn_unknown") == "agent"
    assert log.who(None) == "agent"
