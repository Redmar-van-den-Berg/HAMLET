#!/usr/bin/env python3

import argparse
import json
from filter_vep import Criterion, Variant, VEP
from itertools import zip_longest
from collections import OrderedDict

from typing import Iterator

def read_criteria_file(criteria_file: str) -> OrderedDict:
    """Read the criterions file"""
    annotations = OrderedDict()

    header = None
    with open(criteria_file) as fin:
        for line in fin:
            if line.startswith("#"):
                continue

            spline = line.strip("\n").split("\t")
            if header is None:
                header = spline
                continue

            # Read into dict, convert '' to None
            d = {k: v if v else None for k, v in zip_longest(header, spline)}

            # Check that at least the transcript id is set
            transcript_id = d.get("transcript_id")
            assert transcript_id is not None

            c = Criterion(
                identifier=transcript_id,
                coordinate="c",
                consequence=d["consequence"],
                start=d["start"],
                end=d["end"],
            )
            annotation = d.get("annotation", "")

            annotations[c] = annotation

    return annotations

def parse_vep_json(vep_file: str) -> Iterator[VEP]:
    """Parse the VEP 'json' output file, each line contains a JSON entry"""
    with open(vep_file) as fin:
        for line in fin:
            yield VEP(json.loads(line))

def main(vep_file: str, annotations_file: str):
    criteria = read_criteria_file(annotations_file)

    for vep in parse_vep_json(vep_file):
        for transcript in vep["transcript_consequences"]:
            # Make sure hgvsc is defined
            hgvsc = transcript.get("hgvsc")
            if hgvsc is None:
                continue
            variant = Variant(hgvsc, transcript["consequence_terms"])
            for crit, annotation in criteria.items():
                if crit.match(variant):
                    transcript["annotation"] = annotation
                    break
        print(json.dumps(vep, sort_keys=True))



if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        "Extract genes (and transcript) of interest from VEP output"
    )

    parser.add_argument("--vep", help="VEP json output file", required=True)
    parser.add_argument("--annotations", help="Criteria file with annotations", required=True)

    args = parser.parse_args()

    main(
        args.vep,
        args.annotations
    )
