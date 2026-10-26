"""Interaction with Parsr's REST API"""

import csv
import importlib.resources
import io
import json
import logging
import time
import urllib.error
import urllib.request
import uuid
from pathlib import Path

from .utils import update_dict, write_dict

logger = logging.getLogger(__name__)

TIMEOUT = 120  # seconds per HTTP request, processing time itself is unlimited


def setup_config(config, adjust_cleaner_config, check_tables, fast):
    """Merge pd3f's base config for Parsr with the user's adjustments"""
    # update base config of parsr
    cfg = importlib.resources.files("pd3f").joinpath("pd3fConfig.json")
    jdata = update_dict(json.loads(cfg.read_text()), config)

    # Update parsr cleaner config since it's more complicated.
    # The cleaner consists of a pipeline, so we first have to find the matching module.
    # Then update its configuration.
    for new_cl in adjust_cleaner_config:
        for idx, cl in enumerate(jdata["cleaner"]):
            if not isinstance(cl, list):
                continue
            if cl[0] != new_cl[0]:
                continue
            jdata["cleaner"][idx] = [cl[0], {**cl[1], **new_cl[1]}]

    if not check_tables:
        jdata["cleaner"] = [
            x
            for x in jdata["cleaner"]
            if isinstance(x, str) or "table-detection" not in x[0]
        ]

    if fast:
        jdata["cleaner"] = [
            x
            for x in jdata["cleaner"]
            if _module_name(x) not in ("drawing-detection", "image-detection")
        ]
    return jdata


def _module_name(cleaner):
    return cleaner if isinstance(cleaner, str) else cleaner[0]


def _request(url, data=None, headers=None):
    req = urllib.request.Request(url, data=data, headers=headers or {})
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as response:
            return response.status, response.read().decode()
    except urllib.error.HTTPError as e:
        # Parsr answers with its stderr if processing failed
        detail = e.read().decode(errors="replace")[-2000:]
        raise RuntimeError(f"Parsr: {url} failed with {e.code}: {detail}") from e


def _send_document(api, file_path, config):
    boundary = uuid.uuid4().hex
    parts = [
        ("file", "document.pdf", "application/pdf", Path(file_path).read_bytes()),
        ("config", "config.json", "application/json", json.dumps(config).encode()),
    ]
    body = b"".join(
        f'--{boundary}\r\nContent-Disposition: form-data; name="{name}"; '
        f'filename="{filename}"\r\nContent-Type: {content_type}\r\n\r\n'.encode()
        + content
        + b"\r\n"
        for name, filename, content_type, content in parts
    )
    body += f"--{boundary}--\r\n".encode()
    headers = {"Content-Type": f"multipart/form-data; boundary={boundary}"}
    return _request(f"{api}/document", body, headers)[1]


def _semicolon_to_comma(text):
    out = io.StringIO()
    csv.writer(out, lineterminator="\n").writerows(
        csv.reader(io.StringIO(text), delimiter=";")
    )
    return out.getvalue()


def _get_tables(api, doc_id):
    paths = json.loads(_request(f"{api}/csv/{doc_id}")[1])
    # paths end with /{page}/{table}
    positions = sorted(tuple(map(int, p.rsplit("/", 2)[1:])) for p in paths)
    return [
        _semicolon_to_comma(_request(f"{api}/csv/{doc_id}/{page}/{table}")[1])
        for page, table in positions
    ]


def run_parsr(
    file_path,
    out_dir=None,
    config=None,
    adjust_cleaner_config=(),
    text=False,
    markdown=False,
    check_tables=False,
    fast=False,
    parsr_location="localhost:3001",
    **kwargs,
):
    """Send a PDF to Parsr and wait for the result.

    Returns Parsr's JSON and, if `check_tables`, the tables as CSV strings.
    `out_dir`: also write the results (and `text` / `markdown` if set) to this directory.
    """
    api = f"http://{parsr_location}/api/v1"
    parsr_config = setup_config(config or {}, adjust_cleaner_config, check_tables, fast)
    parsr_config["output"]["formats"]["text"] |= text
    parsr_config["output"]["formats"]["markdown"] |= markdown

    logger.info("sending PDF to Parsr")
    logger.debug(parsr_config)
    doc_id = _send_document(api, file_path, parsr_config)

    # 200 while processing, 201 when done
    while _request(f"{api}/queue/{doc_id}")[0] != 201:
        time.sleep(2)
    logger.info("got response from Parsr")

    data = json.loads(_request(f"{api}/json/{doc_id}")[1])
    tables = _get_tables(api, doc_id) if check_tables else None

    if out_dir is not None:
        out_dir = Path(out_dir) / Path(file_path).stem
        out_dir.mkdir(exist_ok=True, parents=True)

        if text:
            (out_dir / "text.txt").write_text(_request(f"{api}/text/{doc_id}")[1])

        if markdown:
            (out_dir / "text.md").write_text(_request(f"{api}/markdown/{doc_id}")[1])

        for idx, t in enumerate(tables or []):
            (out_dir / f"table_{idx}.csv").write_text(t)

        write_dict(data, out_dir / "data.json")

    return data, tables
