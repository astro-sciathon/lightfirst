from lightfirst.asas_sn import Asas_sn
from lightfirst.ztf_ampel import ZTFQuery
from lightfirst.atlas import Atlas
import pandas as pd
import matplotlib.pyplot as plt
from astropy.time import Time
import yaml
import argparse

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


if __name__ == "__main__":

    # Read in config file for testing
    parser = argparse.ArgumentParser()
    parser.add_argument("config", type=str, help="yaml config file containing token information")
    args = parser.parse_args()

    # Define data sources from config file
    with open(args.config) as stream:
        data_sources = yaml.safe_load(stream)
    
    # Create session
    session = ColibriSession(data_sources)
    # Pull light curves
    lcs = session.query_all(ra=244.00092, dec=22.26803, date_min="2018-06-04", date_max="2018-06-29")
    session.plot_lcs(lcs, title="SN 2018cow")

