"""Step 0 - discover Delhi-NCR monitoring stations through the OpenAQ v3 API.

Writes  data/reference/stations.csv  and  data/reference/sensors.csv.
REVIEW stations.csv by hand afterwards: fix `region` where needs_review == 1 and
drop stations you do not want. Needs OPENAQ_API_KEY (free at https://explore.openaq.org).
Field names follow the OpenAQ v3 docs as I know them; if you hit a KeyError, compare
with https://docs.openaq.org and adjust the parsing below.
"""
import os
import sys
import time

import pandas as pd
import requests

from pipeline.config import REF, STATION_BBOX, NCR_NAME_KEYWORDS, POLLUTANTS

BASE = "https://api.openaq.org/v3"


def api_get(path, params=None):
    key = os.environ.get("OPENAQ_API_KEY")
    if not key:
        sys.exit("Set OPENAQ_API_KEY first (free key from explore.openaq.org).")
    for attempt in range(6):
        r = requests.get(BASE + path, params=params, headers={"X-API-Key": key}, timeout=60)
        if r.status_code == 200:
            return r.json()
        if r.status_code == 429:
            time.sleep(30 * (attempt + 1))
            continue
        r.raise_for_status()
    raise RuntimeError("OpenAQ request failed: " + path)


def region_from_name(name: str):
    n = (name or "").lower()
    if "delhi" in n:
        return "Delhi", 0
    if any(k in n for k in NCR_NAME_KEYWORDS):
        return "NCR", 0
    return "NCR", 1          # unknown -> NCR but flag for manual review


def main():
    bbox = ",".join(str(x) for x in STATION_BBOX)
    stations, sensors, page = [], [], 1
    while True:
        js = api_get("/locations", {"bbox": bbox, "limit": 1000, "page": page})
        results = js.get("results", [])
        for loc in results:
            region, review = region_from_name(loc.get("name"))
            stations.append({
                "station_id": f"OAQ{loc['id']}", "name": loc.get("name"),
                "lat": loc["coordinates"]["latitude"], "lon": loc["coordinates"]["longitude"],
                "region": region, "needs_review": review, "openaq_location_id": loc["id"],
                "provider": (loc.get("provider") or {}).get("name"),
            })
            for s in loc.get("sensors", []):
                p = s["parameter"]["name"]
                if p in POLLUTANTS:
                    sensors.append({"station_id": f"OAQ{loc['id']}", "sensor_id": s["id"],
                                    "parameter": p, "units": s["parameter"].get("units")})
        if len(results) < 1000:
            break
        page += 1
    st = pd.DataFrame(stations)
    sn = pd.DataFrame(sensors)
    # keep only stations that measure PM2.5
    pm_ok = set(sn.loc[sn.parameter == "pm25", "station_id"])
    st = st[st.station_id.isin(pm_ok)].reset_index(drop=True)
    sn = sn[sn.station_id.isin(pm_ok)]
    st.to_csv(REF / "stations.csv", index=False)
    sn.to_csv(REF / "sensors.csv", index=False)
    print(f"{len(st)} PM2.5 stations ({(st.region == 'Delhi').sum()} Delhi, {(st.region == 'NCR').sum()} NCR); "
          f"{int(st.needs_review.sum())} need manual region review -> {REF / 'stations.csv'}")


if __name__ == "__main__":
    main()
