import json
from pathlib import Path
from types import SimpleNamespace

from streamclipper.live import command


class FakeRing:
    def __init__(self, end):
        self.end = end
        self.exports = []

    def export_window(self, start, end, output):
        self.exports.append((start, end, Path(output)))
        Path(output).parent.mkdir(parents=True, exist_ok=True)
        Path(output).write_bytes(b"window")

    def select(self, start, end):
        return [SimpleNamespace(start=0.0)]


def test_live_manual_capture_waits_for_postroll_then_exports(tmp_path, monkeypatch):
    ring = FakeRing(10.0)
    run = command.LiveRun(ring, None, None, None, out_dir=tmp_path)
    req_dir = tmp_path / "capture_requests"
    req_dir.mkdir()
    req = req_dir / "a1b2c3.json"
    req.write_text(json.dumps({"id": "a1b2c3", "start": 5, "end": 12, "status": "queued"}), encoding="utf-8")
    trimmed = []

    def fake_trim(source, start, end, output):
        trimmed.append((Path(source), start, end, Path(output)))
        Path(output).write_bytes(b"clip")
        return Path(output)

    monkeypatch.setattr(command, "trim_video", fake_trim)
    run._service_manual_captures()
    assert json.loads(req.read_text(encoding="utf-8"))["status"] == "queued"
    assert not trimmed

    ring.end = 13.0
    run._service_manual_captures()
    result = json.loads(req.read_text(encoding="utf-8"))
    assert result["status"] == "done"
    assert result["output"] == "manual_live_a1b2c3.mp4"
    assert trimmed and trimmed[0][1:3] == (5.0, 12.0)
