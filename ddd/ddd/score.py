import time

import requests


def score_perplexity(texts, verbose=True):
    if type(texts) is str:
        texts = [texts]

    r = requests.post("http://ddd-flair.app.vis.one/score_async", json={"texts": texts})
    if r.status_code == 200:
        job_id = r.json()["id"]
        score = None
        while True:
            final_res = requests.get("http://ddd-flair.app.vis.one/results/" + job_id)
            if final_res.status_code == 202:
                time.sleep(1)
                verbose and print("waiting for result")
            else:
                score = final_res.json()
                break
    else:
        r.raise_for_status()
    return score
