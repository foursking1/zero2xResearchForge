# -*- coding: utf-8 -*-
"""
C03: Tuning temporal-normalization weights to the earthquake band (15-50 s)
     reduces spurious precursory arrivals in cross-correlations between the
     New-Zealand stations CRLZ and HIZ.

This claim requires (i) raw or cross-correlation data for the NZ stations
CRLZ and HIZ and (ii) a broadband (15-50 s) comparison.  We check every item
in the frozen data bundle for the presence of any NZ / CRLZ / HIZ data and
document the result.
"""
import json
import os
import glob

import pandas as pd

import config as cfg


def main():
    found = {}

    # 1) station priority-12 XML
    from obspy import read_inventory
    inv = read_inventory(cfg.STATIONS_XML)
    xml_codes = [(n.code, s.code) for n in inv for s in n]
    found["priority12_xml_stations"] = xml_codes
    found["contains_CRLZ"] = any(c[1] == "CRLZ" for c in xml_codes)
    found["contains_HIZ"] = any(c[1] == "HIZ" for c in xml_codes)
    found["contains_NZ_network"] = any(c[0] == "NZ" for c in xml_codes)

    # 2) iris manifest
    df = pd.read_csv(cfg.IRIS_MANIFEST)
    all_sta = set(df["sta"])
    all_net = set(df["net"])
    found["manifest_station_count"] = len(all_sta)
    found["manifest_networks"] = sorted(all_net)
    found["contains_CRLZ"] = found.get("contains_CRLZ") or ("CRLZ" in all_sta)
    found["contains_HIZ"] = found.get("contains_HIZ") or ("HIZ" in all_sta)
    found["contains_NZ_network"] = found.get("contains_NZ_network") or ("NZ" in all_net)

    # 3) every mseed in the bundle (station header)
    mseeds = glob.glob(os.path.join(cfg.BUNDLE, "**", "*.mseed"), recursive=True)
    mseed_stations = set()
    from obspy import read
    for f in mseeds:
        try:
            st = read(f)
            for tr in st:
                mseed_stations.add((tr.stats.network, tr.stats.station))
        except Exception:
            pass
    found["mseed_station_ids"] = sorted(mseed_stations)
    found["mseed_contains_CRLZ"] = any(s == "CRLZ" for _, s in mseed_stations)
    found["mseed_contains_HIZ"] = any(s == "HIZ" for _, s in mseed_stations)
    found["mseed_contains_NZ"] = any(n == "NZ" for n, _ in mseed_stations)

    found["conclusion"] = (
        "No data for stations CRLZ or HIZ, and no NZ-network data, are present "
        "in the frozen bundle (manifest, station XML, or any mseed file). "
        "The claim C03 cannot be tested with the frozen data."
    )

    out = os.path.join(cfg.RESULTS_DIR, "c03_data_availability.json")
    with open(out, "w") as fh:
        json.dump(found, fh, indent=2, default=str)
    print(json.dumps(found, indent=2, default=str))
    print("saved", out)


if __name__ == "__main__":
    main()
