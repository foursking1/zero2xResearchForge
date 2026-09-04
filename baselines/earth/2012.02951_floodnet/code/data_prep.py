"""Prepare the frozen training/development/evaluation split.

Splits at the IMAGE level (no image ever appears in both training and
evaluation) with a fixed seed, so the evaluation subset cannot leak into
training. Dev set (for model selection) is carved out of the training images.

Outputs
-------
results/split.json : image ids per split, QA-ids per split, and proportions.
"""
import json
import os

import numpy as np

import config


def main():
    with open(config.VQA_TRAIN_JSON) as f:
        qa = json.load(f)

    qa_list = [v for v in qa.values()]
    for v in qa_list:
        v["id"] = str(v["Image_ID"]) + "##" + str(v["Question"]) + "##" + str(v["Ground_Truth"])

    images = sorted({v["Image_ID"] for v in qa_list})

    rng = np.random.RandomState(config.SEED)
    order = rng.permutation(len(images))
    n_eval = int(round(config.EVAL_FRAC * len(images)))
    eval_imgs = set(images[i] for i in order[:n_eval])
    train_imgs = set(images[i] for i in order[n_eval:])

    # dev carved out of train images (for model selection only)
    train_order = sorted(train_imgs)
    rng2 = np.random.RandomState(config.SEED + 1)
    dev_order = rng2.permutation(len(train_order))
    n_dev = int(round(config.DEV_FRAC_OF_TRAIN * len(train_order)))
    dev_imgs = set(train_order[i] for i in dev_order[:n_dev])
    train_imgs = set(train_order[i] for i in dev_order[n_dev:])

    split_qa = {"train": [], "dev": [], "eval": [], "all": []}
    for v in qa_list:
        if v["Image_ID"] in eval_imgs:
            split_qa["eval"].append(v)
        elif v["Image_ID"] in dev_imgs:
            split_qa["dev"].append(v)
        else:
            split_qa["train"].append(v)
        split_qa["all"].append(v)

    # sanity: no image overlap across splits
    def imset(lst):
        return {v["Image_ID"] for v in lst}

    assert not (imset(split_qa["train"]) & imset(split_qa["dev"]))
    assert not (imset(split_qa["train"]) & imset(split_qa["eval"]))
    assert not (imset(split_qa["dev"]) & imset(split_qa["eval"]))

    summary = {}
    for split in ("train", "dev", "eval"):
        lst = split_qa[split]
        from collections import Counter

        cnt = Counter(v["Question_Type"] for v in lst)
        summary[split] = {
            "n_qa": len(lst),
            "n_images": len(imset(lst)),
            "by_type": dict(cnt),
        }
    summary["answer_vocab_size"] = len({str(v["Ground_Truth"]) for v in qa_list})
    summary["image_split"] = {"seed": config.SEED, "eval_fraction": config.EVAL_FRAC,
                              "n_train_images": len(train_imgs), "n_dev_images": len(dev_imgs),
                              "n_eval_images": len(eval_imgs)}

    # make ids deterministic and JSON-serializable
    serializable = {
        "meta": summary,
        "split_qa": {k: [{"Image_ID": v["Image_ID"], "Question": v["Question"],
                          "Ground_Truth": str(v["Ground_Truth"]),
                          "Question_Type": v["Question_Type"]} for v in lst]
                     for k, lst in split_qa.items()},
        "split_images": {"train": sorted(train_imgs), "dev": sorted(dev_imgs),
                         "eval": sorted(eval_imgs)},
    }
    out = os.path.join(config.RESULTS_DIR, "split.json")
    with open(out, "w") as f:
        json.dump(serializable, f, indent=2, ensure_ascii=False)
    print(json.dumps(summary, indent=2))
    print("wrote", out)


if __name__ == "__main__":
    main()