import json
from pathlib import Path

from parsr_client import ParsrClient as client

parsr = client("localhost:3001")

job = parsr.send_document(
    file="011020_Stellungnahme_DRB_RefE__Belaempfung-Rechtsextremismus-Hasskriminalitaet.pdf",
    config="defaultConfig.json",
    document_name="Sample File2",
    wait_till_finished=True,
    save_request_id=True,
)

Path("out/text.txt").write_text(parsr.get_text())
Path("out/text.md").write_text(parsr.get_markdown())

with open("out/data.json", "w", encoding="utf-8") as f:
    json.dump(parsr.get_json(), f, ensure_ascii=False, indent=4)
