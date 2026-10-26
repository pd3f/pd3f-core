import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest

from pd3f.parsr_wrapper import _module_name, run_parsr, setup_config

CSV = {"1/2": "c;d\n", "1/10": "e;f\n", "2/1": 'Preis;"1,20"\n'}


class FakeParsr(BaseHTTPRequestHandler):
    fail = False
    polls = 0
    received = None

    def do_POST(self):
        FakeParsr.received = self.rfile.read(int(self.headers["Content-Length"]))
        self.answer(202, "doc1")

    def do_GET(self):
        path = self.path.removeprefix("/api/v1/")
        if path == "queue/doc1":
            if FakeParsr.fail:
                self.answer(500, "Error: pdfminer crashed")
                return
            FakeParsr.polls += 1
            self.answer(201 if FakeParsr.polls > 1 else 200, "{}")
        elif path == "json/doc1":
            self.answer(200, json.dumps({"pages": []}))
        elif path == "csv/doc1":
            self.answer(200, json.dumps([f"/api/v1/csv/doc1/{k}" for k in CSV]))
        elif path.startswith("csv/doc1/"):
            self.answer(200, CSV[path.removeprefix("csv/doc1/")])
        elif path == "text/doc1":
            self.answer(200, "plain text")
        else:
            self.answer(404, "not found")

    def answer(self, status, body):
        self.send_response(status)
        self.end_headers()
        self.wfile.write(body.encode())

    def log_message(self, *args):
        pass


@pytest.fixture
def parsr(monkeypatch):
    monkeypatch.setattr("pd3f.parsr_wrapper.time.sleep", lambda _: None)
    FakeParsr.fail, FakeParsr.polls, FakeParsr.received = False, 0, None
    server = ThreadingHTTPServer(("127.0.0.1", 0), FakeParsr)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    yield f"127.0.0.1:{server.server_port}"
    server.shutdown()


@pytest.fixture
def pdf(tmp_path):
    path = tmp_path / "in.pdf"
    path.write_bytes(b"%PDF-1.4 fake")
    return path


def names(cfg):
    return [_module_name(x) for x in cfg["cleaner"]]


def test_setup_config_drops_modules():
    full = names(setup_config({}, (), check_tables=True, fast=False))
    assert {"drawing-detection", "image-detection", "table-detection"} <= set(full)

    fast = names(setup_config({}, (), check_tables=False, fast=True))
    assert not {"drawing-detection", "image-detection"} & set(fast)
    assert not [x for x in fast if "table-detection" in x]
    assert "lines-to-paragraph" in fast


def test_setup_config_adjusts_cleaner():
    cfg = setup_config({}, [["whitespace-removal", {"minWidth": 99}]], True, False)
    module = next(x for x in cfg["cleaner"] if _module_name(x) == "whitespace-removal")
    assert module[1]["minWidth"] == 99


def test_run_parsr(parsr, pdf, tmp_path):
    data, tables = run_parsr(
        pdf,
        out_dir=tmp_path / "out",
        text=True,
        check_tables=True,
        parsr_location=parsr,
    )

    assert data == {"pages": []}
    # ordered numerically by page and table, converted to comma-separated CSV
    assert tables == ["c,d\n", "e,f\n", 'Preis,"1,20"\n']
    assert b"%PDF-1.4 fake" in FakeParsr.received
    assert b'"text": true' in FakeParsr.received

    out = tmp_path / "out" / "in"
    assert (out / "text.txt").read_text() == "plain text"
    assert (out / "table_2.csv").read_text() == 'Preis,"1,20"\n'
    assert json.loads((out / "data.json").read_text()) == data


def test_run_parsr_without_tables(parsr, pdf):
    assert run_parsr(pdf, parsr_location=parsr) == ({"pages": []}, None)


def test_run_parsr_failure(parsr, pdf):
    FakeParsr.fail = True
    with pytest.raises(RuntimeError, match="failed with 500: Error: pdfminer crashed"):
        run_parsr(pdf, parsr_location=parsr)
