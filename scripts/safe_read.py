"""Reads that do not silently destroy 'NA', 'null', 'None' and friends.

pandas.read_csv converts a documented list of tokens to NaN by default. MedMentions instance
mm_0046685 has the two-character gold_mention 'NA' (the abbreviation in "total AgNOR area /
nuclear area (TAA / NA)"), and every default read turned it into a missing value. 15 MedMentions
instances are affected (12 'NA', 3 'null'); gold_mention is the key for rule 1 of the five-rule
assignment, so those rows were assigned by a different path than intended.

Only the empty string is treated as missing here. Everything else is data.

Usage:
    from scripts.safe_read import read_csv_strict
    df = read_csv_strict(path, usecols=[...])
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

# The tokens pandas would otherwise swallow. Kept for tests and for reporting.
PANDAS_DEFAULT_NA = {
    "", "#N/A", "#N/A N/A", "#NA", "-1.#IND", "-1.#QNAN", "-NaN", "-nan", "1.#IND",
    "1.#QNAN", "<NA>", "N/A", "NA", "NULL", "NaN", "None", "n/a", "nan", "null",
}


def read_csv_strict(path, **kwargs):
    """read_csv where an empty cell is missing and every other token is a literal string."""
    kwargs.setdefault("low_memory", False)
    kwargs["keep_default_na"] = False
    # float_precision: pandas' default and "high" both parse some float64 values 1 ULP away
    # from what the file contains; only "round_trip" returns the written value. A reader that
    # copies a float column from one artefact into another therefore degrades it. Default it
    # here so every caller of this wrapper is faithful, and let an explicit kwarg override.
    # See provenance/reading_hazards_note.txt.
    kwargs.setdefault("float_precision", "round_trip")
    kwargs["na_values"] = [""]
    return pd.read_csv(path, **kwargs)
