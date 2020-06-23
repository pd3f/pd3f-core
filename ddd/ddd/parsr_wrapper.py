import json
import tempfile
from pathlib import Path
import importlib.resources

from parsr_client import ParsrClient as client


from .utils import update_dict, write_dict


def run_parsr(
    file_path, out_dir=None, cleaner_config=[], config={}, text=False, markdown=False
):
    parsr = client("localhost:3001")

    # update base config of parsr
    with importlib.resources.path("ddd", "dddConfig.json") as cfg_path:
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

    with tempfile.NamedTemporaryFile(mode="w+") as tmp_config:
        json.dump(jdata, tmp_config)
        tmp_config.flush()  # persist

        # TODO: when upgrading to v3.2, use file_path and config_path
        parsr.send_document(
            file=file_path,
            config=tmp_config.name,
            wait_till_finished=True,
            save_request_id=True,
            silent=False,
        )

    if not out_dir is None:
        out_dir = Path(out_dir) / Path(file_path).stem
        out_dir.mkdir(exist_ok=True, parents=True)

        if text:
            (out_dir / "text.txt").write_text(parsr.get_text())

        if markdown:
            (out_dir / "text.md").write_text(parsr.get_markdown())

        write_dict(parsr.get_json(), out_dir / "data.json")
    return parsr.get_json()
