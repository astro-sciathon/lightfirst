import pandas as pd


class DataSource():
    """
    Base class for a data sources.
    Allows ColibriSession object to interact with data sources
    """
    def __init__(self, auth_info=None):
        """
        Create a DataSource object.
        :param auth_info: dictionary containing any token/auth information.
        """

        self.auth_info = auth_info

    def get_lc(self, ra, dec, date_min, date_max):
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
        return pd.DataFrame(columns=['obj_id','mjd', 'mag', 'mag_err', 'filter',
                                     'limit'])

