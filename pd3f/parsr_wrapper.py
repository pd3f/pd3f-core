"""Wrapper to interaction with parsr (using parsr's Python client)
"""

import importlib.resources
import json
import logging
import tempfile
from pathlib import Path

from parsr_client import ParsrClient as client

from .utils import update_dict, write_dict

logger = logging.getLogger(__name__)


def run_parsr(
    file_path,
    out_dir=None,
    cleaner_config=[],
    config={},
    text=False,
    markdown=False,
    check_tables=False,
    fast=False,
    parsr_location="localhost:3001",
    **kwargs,
):
    """Wrapper to interaction with parsr (using parsr's Python client)

    TODO: consider lang? Or not important because we don't use pars'r OCR?
    """
    parsr = client(parsr_location)

    # update base config of parsr
    with importlib.resources.path("pd3f", "pd3fConfig.json") as cfg_path:
        jdata = json.loads(cfg_path.read_text())
    jdata = update_dict(jdata, config)

    # Update parsr cleaner config since it's more complicated.
    # The cleaner consists of a pipeline, so we first have to find the matching module.
    # Then update its configuration.
    for new_cl in cleaner_config:
        for idx, cl in enumerate(jdata["cleaner"]):
            if type(cl) != list:
                continue
            if cl[0] != new_cl[0]:
                continue
            jdata["cleaner"][idx] = [cl[0], {**cl[1], **new_cl[1]}]

    if not check_tables:
        jdata["cleaner"] = [
            x
            for x in jdata["cleaner"]
            if type(x) is str or "table-detection" not in x[0]
        ]

    if fast:
        jdata["cleaner"] = [
            x
            for x in jdata["cleaner"]
            if type(x) is str and x != "drawing-detection" or x[0] != "image-detection"
        ]

    with tempfile.NamedTemporaryFile(mode="w+") as tmp_config:
        json.dump(jdata, tmp_config)
        tmp_config.flush()  # persist

        # TODO: when upgrading to v3.2, use file_path and config_path
        logger.info("sending PDF to Parsr")

        logger.debug(jdata)

        parsr.send_document(
            file=file_path,
            config=tmp_config.name,
            wait_till_finished=True,
            save_request_id=True,
            silent=False,
        )

    logger.info("got response from Parsr")

    tables = []
    if check_tables:
        for page, table in parsr.get_tables_info():
            # table gets returned as panda df
            tables.append(parsr.get_table(page=page, table=table))

    if not out_dir is None:
        out_dir = Path(out_dir) / Path(file_path).stem
        out_dir.mkdir(exist_ok=True, parents=True)

        if text:
            (out_dir / "text.txt").write_text(parsr.get_text())

        if markdown:
            (out_dir / "text.md").write_text(parsr.get_markdown())

        if check_tables:
            for idx, t in enumerate(tables):
                (out_dir / f"table_{idx}.csv").write_text(t.to_csv())

        write_dict(parsr.get_json(), out_dir / "data.json")

    if not check_tables:
        return parsr.get_json(), None
    return parsr.get_json(), [x.to_csv() for x in tables]

