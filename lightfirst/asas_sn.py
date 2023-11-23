from pyasassn.client import SkyPatrolClient
import pandas as pd

class Asas_sn(DataSource):
    """
    Object that allows ColibriSession to query ASAS-SN forced photometry.
    """
    def __init__(self, auth_info):
        """
        Create a ASAS-SN DataSource object.
        """
        super().__init__(auth_info)
        self.name = 'asas-sn'

        # Create client
        self.client = SkyPatrolClient(verbose=False)

    def get_lc(self, ra, dec, mjd_min, mjd_max):
        """
        Method that pulls a lightcurve from the given data source.
        :param ra: right ascention of target in decimal degrees; float.
        :param dec: declination of target in decimal degrees; float.
        :date_min: minimum modified julian date for light curve data; float.
        :date_max: maximum modified julian date for light curve data; float.
        :return: pandas data frame containing light curve, with columns;
                  obj_id: object id for the row
                    (certain surveys my return multiple objects per location).
                  mjd: modified julian date of observation.
                  mag: measured magnitude of observation.
                  mag_err: magnitude error of observation.
                  filter: filter used for observation.
                  limit: limiting magnitude at observation.
        """
        try:
            lcs = self.client.cone_search(ra, dec, radius=7.5, units='arcsec', download=True)
            idx = lcs.data.asas_sn_id.unique()[0]
        except:
            return pd.DataFrame(columns=['obj_id','mjd', 'mag', 'mag_err', 'filter','limit'])

        lightcurve = lcs[idx].data
        phot = pd.DataFrame(lightcurve, columns =['asas_sn_id','jd', 'flux', 'flux_err', 'mag', 'mag_err', 'phot_filter', 'limit'])
        # Convert id column name
        phot.rename({'asas_sn_id': 'obj_id'})
        # MJD Conversion
        phot['mjd'] = phot['jd'] - 2400000.5
        phot.rename(columns={"phot_filter": "filter"}, inplace=True)
        # Cut on mjd
        phot = phot[(mjd_min <= phot['mjd']) & (phot['mjd'] <= mjd_max)]

        return phot
