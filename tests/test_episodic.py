"""Episodic memory (SQLite) testleri."""


def test_log_and_recent(isolated_episodic):
    ep = isolated_episodic
    ep.log_event("Test olayı", category="system")
    ctx = ep.get_recent_context(hours=1)
    assert "Test olay" in ctx


def test_log_command_ok_flag(isolated_episodic):
    ep = isolated_episodic
    ep.log_command("good_tool", "x=1", ok=True)
    ep.log_command("bad_tool", "y=2", ok=False)
    hints = ep.get_tool_hints(days=1)
    assert "good_tool" in hints
    assert "bad_tool" not in hints  # başarısızlar hint'e girmez


def test_today_summary(isolated_episodic):
    ep = isolated_episodic
    assert "yok" in ep.get_today_summary()
    ep.log_event("ilk olay")
    s = ep.get_today_summary()
    assert "1 olay" in s


def test_cleanup_old(isolated_episodic):
    ep = isolated_episodic
    ep.log_event("bugün")
    removed = ep.cleanup_old(keep_days=30)
    assert removed == 0  # bugünkü silinmemeli


def test_available_days(isolated_episodic):
    ep = isolated_episodic
    ep.log_event("x")
    days = ep.get_available_days()
    assert len(days) == 1
