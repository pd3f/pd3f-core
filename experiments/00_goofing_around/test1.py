from pathlib import Path

import ddd

for p in Path("../../data/bmjv/").glob("*.pdf"):
    if p.name.startswith("00003"):
        print(p.name)
        # ddd.run_parsr(
        #     str(p),
        #     out_dir="out/",
        #     cleaner_config=[["reading-order-detection", {"minVerticalGapWidth": 20}]],
        # )

        e = ddd.Export(f"out/{p.stem}/data.json")
        e.save_markdown(f"out/{p.stem}/clean.md")


# run.do_parsr(
#     "../data/bmjv/00001_112018_FU_Berlin_Richtlinie_2017_1371.pdf",
#     out_dir="out2",
#     cleaner_config=[["reading-order-detection", {"minVerticalGapWidth": 20}]],
# )


# run.do_parsr(
#     "../data/bmjv/01384_011020_Stellungnahme_DRB_RefE__Belaempfung-Rechtsextremismus-Hasskriminalitaet.pdf",
#     out_dir="out1",

#     cleaner_config=[["reading-order-detection", {"minVerticalGapWidth": 10}]],
# )


# output.save(
#     "out1/01384_011020_Stellungnahme_DRB_RefE__Belaempfung-Rechtsextremismus-Hasskriminalitaet/data.json",
#     "d.txt",
# )
