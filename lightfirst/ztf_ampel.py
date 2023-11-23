import pandas as pd
import requests
from typing import Final

from lightfirst.data_source import DataSource


class ZTFQuery(DataSource):
    MJD_OFFSET: float = 2400000.5

    API_ENDPOINT: Final[str] = "https://ampel.zeuthen.desy.de/api/ztf/archive/v3"

    def __init__(self, auth_info):
        # self.token = token_info
        super().__init__(auth_info)
        self.name = "ztf"
        self.header = {
            "Authorization": "bearer " + self.auth_info,
            "Accept": "application/json",
        }

    def get_lc(self, ra: float, dec: float, date_min: float, date_max: float):
        MJD_OFFSET: float = 2400000.5
        mjd_start = date_min
        mjd_end = date_max

        jd_start = mjd_start + self.MJD_OFFSET
        jd_end = mjd_end + self.MJD_OFFSET

        objects = self.cone(
            ra=ra, dec=dec, radius=1 / 3600, jd_start=jd_start, jd_end=jd_end
        )

        lightcurves = []

        for objectid in objects:
            print(f"Querying object {objectid}")
            light = self.photo(objectid=objectid, jd_start=jd_start, jd_end=jd_end)
            lightcurves.append(light)
            # lightcurves.append(light.text)

        return pd.concat(lightcurves)

    def cone(
        self, ra: float, dec: float, radius: float, jd_start: float, jd_end: float
    ):
        ROUTE = self.API_ENDPOINT + "/objects/cone_search"
        query = {
            "ra": ra,
            "dec": dec,
            "radius": radius,
            "jd_start": jd_start,
            "jd_end": jd_end,
        }
        response = requests.get(ROUTE, headers=self.header, params=query)
        return response.json()

    def photo(self, objectid, jd_start, jd_end):
        ROUTE = self.API_ENDPOINT + f"/object/{objectid}/photopoints"

        query = {
            "jd_start": jd_start,
            "jd_end": jd_end,
        }

        response = requests.get(ROUTE, headers=self.header, params=query)

        data = response.json()

        datapoints = data["prv_candidates"]

        df = pd.DataFrame(datapoints)

        out = pd.DataFrame(
            columns=["obj_id", "mjd", "mag", "mag_err", "filter", "limit"]
        )

        out["mjd"] = df["jd"] - self.MJD_OFFSET
        out["mag"] = df["magpsf"]
        out["mag_err"] = df["sigmapsf"]
        out["filter"] = df["fid"].map({1: "g", 2: "r", 3: "i"})
        out["limit"] = df["diffmaglim"]
        out["obj_id"] = objectid

        return out
