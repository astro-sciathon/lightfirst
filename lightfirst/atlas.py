import pandas as pd
import time
import requests
import numpy as np
from lightfirst.data_source import DataSource

class Atlas(DataSource):
    """
    Object that allows ColibriSession to query ATLAS forced photometry.
    """
    def __init__(self, auth_info):
        """
        Create a Atlas DataSource object.
        :param auth_info: dictionary containing any token/auth information.
        """
        super().__init__(auth_info)
        self.name = 'atlas'

    def get_lc(self, ra, dec, mjd_min, mjd_max):
        """
        Method that pulls a lightcurve from the given data source.
        :param ra: right ascention of target in decimal degrees; float.
        :param dec: declination of target in decimal degrees; float.
        :mjd_min: minimum modified julian date for light curve data; float.
        :mjd_max: maximum modified julian date for light curve data; float.
        :return: pandas data frame containing light curve, with columns;
                  obj_id: object id for the row
                    (certain surveys my return multiple objects per location).
                  mjd: modified julian date of observation.
                  mag: measured magnitude of observation.
                  mag_err: magnitude error of observation.
                  filter: filter used for observation.
                  limit: limiting magnitude at observation.
        """

        BASEURL = "https://fallingstar-data.com/forcedphot"
        resp = requests.post(url=f"{BASEURL}/api-token-auth/",
                             data={'username': self.auth_info["username"],
                                   'password': self.auth_info["password"]})

        if resp.status_code == 200:
           token = resp.json()['token']
           #print(f'Your token is {token}')
           headers = {'Authorization': f'Token {token}', 'Accept': 'application/json'}
        else:
           print(f'ERROR {resp.status_code}')
           print(resp.json())

        task_url = None
        while not task_url:
            with requests.Session() as s:
                resp = s.post(f"{BASEURL}/queue/", headers=headers, data={
                    'ra': ra, 'dec': dec, 'mjd_min': mjd_min, 'mjd_max': mjd_max})

                if resp.status_code == 201:  # successfully queued
                    task_url = resp.json()['url']
                    print(f'The task URL is {task_url}')
                elif resp.status_code == 429:  # throttled
                    message = resp.json()["detail"]
                    print(f'{resp.status_code} {message}')
                    t_sec = re.findall(r'available in (\d+) seconds', message)
                    t_min = re.findall(r'available in (\d+) minutes', message)
                    if t_sec:
                        waittime = int(t_sec[0])
                    elif t_min:
                        waittime = int(t_min[0]) * 60
                    else:
                        waittime = 10
                    print(f'Waiting {waittime} seconds')
                    time.sleep(waittime)
                else:
                    print(f'ERROR {resp.status_code}')
                    print(resp.json())


        result_url = None

        while not result_url:
                with requests.Session() as s:

                    if result_url is None:
                        return pd.DataFrame(columns=['obj_id','mjd', 'mag', 'mag_err', 'filter',
                                     'limit'])

                    resp = s.get(task_url, headers=headers)

                    if resp.status_code == 200:  # HTTP OK
                        if resp.json()['finishtimestamp']:
                            result_url = resp.json()['result_url']
                            print(f"Task is complete with results available at {result_url}")
                            break
                        elif resp.json()['starttimestamp']:
                            print(f"Task is running (started at {resp.json()['starttimestamp']})")
                        else:
                            print("Waiting for job to start. Checking again in 10 seconds...")
                        time.sleep(10)
                    else:
                        raise RuntimeError(f'ERROR {resp.json()}')

        with requests.Session() as s:
            print(result_url)
            textdata = s.get(result_url, headers=headers).text

        dfresult = pd.read_csv(io.StringIO(textdata.replace("###", "")), delim_whitespace=True)
        phot_df = dfresult[["MJD","m","dm", "F"]]
        mask = phot_df['m'] < 0 #remove the negative m values (ATLAS does reference images)
        phot_df = phot_df[~mask]
        phot_df.insert(4, "Limit", np.full(len(phot_df), 19.7), True)
        phot_df = phot_df.rename(columns=
                                    {"MJD": "mjd",
                                     "m": "mag",
                                     "dm":"mag_err",
                                     "F":"filter",
                                     "Limit":"limit"})

        return phot_df
