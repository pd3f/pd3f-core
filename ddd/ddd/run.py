import json
import tempfile
from pathlib import Path
import importlib.resources

from parsr_client import ParsrClient as client


from .utils import update_dict, write_dict


def do_parsr(file, out_dir="out", cleaner_config=[], config={}):
    # complicated config for cleaner

    out_dir = Path(out_dir) / Path(file).stem
    out_dir.mkdir(exist_ok=True, parents=True)

    parsr = client("localhost:3001")

    with importlib.resources.path("ddd", "dddConfig.json") as cfg_path:
        jdata = json.loads(cfg_path.read_text())
    jdata = update_dict(jdata, config)

    # update cleaner config
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

        parsr.send_document(
            file=file,
            config=tmp_config.name,
            wait_till_finished=True,
            save_request_id=True,
        )

        (out_dir / "text.txt").write_text(parsr.get_text())
        (out_dir / "text.md").write_text(parsr.get_markdown())

        write_dict(parsr.get_json(), out_dir / "data.json")


# do_parsr(
#     "files/011020_Stellungnahme_DRB_RefE__Belaempfung-Rechtsextremismus-Hasskriminalitaet.pdf"
# )

# do_parsr(
#     "files/011020_Stellungnahme_DRB_RefE__Belaempfung-Rechtsextremismus-Hasskriminalitaet.pdf",
#     out_dir="out2",
#     cleaner_config=[["reading-order-detection", {"minVerticalGapWidth": 20}]],
# )
