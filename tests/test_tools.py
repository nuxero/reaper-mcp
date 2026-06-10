"""Representative tool tests across domains, with REAPER mocked.

These verify the two things every glue tool must get right: the REAPER function name +
argument marshalling it sends, and that it returns the bridge response unchanged.
"""

import asyncio

import pytest

import reaper_mcp_server as srv


def run(coro):
    return asyncio.run(coro)


# --- pure helper (no mock needed) ---

def test_db_to_linear():
    assert srv.db_to_linear(0) == pytest.approx(1.0)
    assert srv.db_to_linear(-6.0) == pytest.approx(0.50119, rel=1e-3)
    assert srv.db_to_linear(-200) == 0  # floored below -150 dB


# --- pass-through tools ---

def test_get_track_count(reaper):
    run(srv.get_track_count())
    assert reaper.last == ("CountTracks", [0])


def test_transport(reaper):
    run(srv.play())
    assert reaper.last == ("OnPlayButton", [])
    run(srv.stop())
    assert reaper.last == ("OnStopButton", [])


def test_get_tempo(reaper):
    run(srv.get_tempo())
    assert reaper.last == ("Master_GetTempo", [])


def test_set_tempo(reaper):
    run(srv.set_tempo(120.0))
    assert reaper.last == ("SetCurrentBPM", [0, 120.0, True])


# --- argument marshalling ---

def test_set_track_pan(reaper):
    run(srv.set_track_pan(1, 0.5))
    assert reaper.last == ("SetMediaTrackInfo_Value", [1, "D_PAN", 0.5])


def test_set_track_mute_bool_to_int(reaper):
    run(srv.set_track_mute(2, True))
    assert reaper.last == ("SetMediaTrackInfo_Value", [2, "B_MUTE", 1])
    run(srv.set_track_mute(2, False))
    assert reaper.last == ("SetMediaTrackInfo_Value", [2, "B_MUTE", 0])


def test_set_track_volume_db_conversion(reaper):
    run(srv.set_track_volume(0, -6.0))
    func, args = reaper.last
    assert func == "SetMediaTrackInfo_Value"
    assert args[0] == 0
    assert args[1] == "D_VOL"
    assert args[2] == pytest.approx(0.50119, rel=1e-3)  # dB -> linear


def test_add_marker(reaper):
    run(srv.add_marker(5.0, "Chorus"))
    assert reaper.last == ("AddProjectMarker2", [0, False, 5.0, 0, "Chorus", -1, 0])


# --- response propagation ---

def test_response_is_returned_unchanged(reaper):
    reaper.response = {"ok": True, "ret": 9}
    assert run(srv.get_track_count()) == {"ok": True, "ret": 9}
