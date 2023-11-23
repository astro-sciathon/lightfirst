from .asas_sn import Asas_sn
from .ztf_ampel import ZTFQuery
from .atlas import Atlas
import pandas as pd
import matplotlib.pyplot as plt
from astropy.time import Time

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


class ColibriSession:
    """
    Base class for retrieving a light curve for a given target by RA and Dec
    from multiple databases.
    """
    DATA_SOURCES = {
                    'atlas': Atlas,
                    'asas-sn': Asas_sn,
                    'ztf': ZTFQuery,
                  }
    CMAP = {'atlas o': 'orange',
            'atlas c': 'cyan',
            'asas-sn g': 'royalblue',
            'asas-sn V': 'green',
            'ztf g': 'blueviolet',
            'ztf r':'olive',
            'ztf i': 'sienna'
            }
    def __init__(self, data_sources):
        """
        Create ColibriSession that allows user to query data sources for lightcurves.
        :param data_sources: dictionary providing information on data sources and
                              their accompanying authorization info.
        :return ColibriSession object.
        """

        # Make the database name uniform: lowercase and no spaces.
        self.data_sources = [ColibriSession.DATA_SOURCES[source_name](auth_info)
                              for source_name, auth_info in data_sources.items()]

    def query_all(self, ra, dec, date_min, date_max):
        """
        Query all data sources for optical light curves at the given coordinates
        within the dates provided
        :param ra: right ascention of target in decimal degrees; float.
        :param dec: declination of target in decimal degrees; float.
        :param date_min: human readable (YYYY-MM-DD) date string for min observation date.
        :param date_max: human readable (YYYY-MM-DD) date string for max observation date.

        :return: dictionary of pandas data frames containing light curves, with columns;
                  obj_id: object id for the row
                    (certain surveys my return multiple objects per location).
                  mjd: modified julian date of observation.
                  mag: measured magnitude of observation.
                  mag_err: magnitude error of observation.
                  filter: filter used for observation.
                  limit: limiting magnitude at observation.
        """

        t1 = Time(date_min)
        mjd_min = t1.mjd
        t2 = Time(date_max)
        mjd_max = t2.mjd

        object_phot = dict()

        for data_source in self.data_sources:
             lc = data_source.get_lc(ra, dec, mjd_min, mjd_max)
             object_phot[data_source.name] = lc

        return object_phot


    def plot_lcs(self, object_phot, title):
        """
        Plots light curves in result set from data sources.
        :param object_phot: dictionary of pandas data frames containing light curves.
                            returned by query_all()
        :param title: title string for plot.
        """
        fig = plt.figure(1)
        fig.clf()
        ax = fig.add_subplot()
        plt.title(title)
        ax.set_ylim([10, 25])
        for source_name, phot in object_phot.items():
            if phot is None:
                continue
            filters = phot['filter'].unique()
            for f_name in filters:
                phot_f = phot[phot['filter'] == f_name]
                filter_label = f"{source_name} {f_name}"

                ax.errorbar(phot_f['mjd'], phot_f['mag'], yerr=phot_f['mag_err'],
                                linestyle='None', marker='o',
                                color=ColibriSession.CMAP[filter_label],
                                label=filter_label)
        ax.set_xlabel("MJD")
        ax.set_ylabel("m")
        ax.invert_yaxis()
        ax.grid()
        ax.legend(numpoints=1)


        plt.draw()
        plt.show()

