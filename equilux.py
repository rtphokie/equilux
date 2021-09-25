'''
Calculate Equilux dates around the March and September Equinoxes for Raleigh, NC
@author: Tony rice
'''
import unittest
import ephem
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

raleigh = ephem.Observer()
raleigh.pressure = 0  # ignoring air pressure differences (unpredicatble)
raleigh.horizon = '-0:34'  # sea-level atmospheric refraction of 34 arc minutes per USNO standard
raleigh.lat, raleigh.lon = '33.78', '-78.64'  # this is home
sun = ephem.Sun()


def sunrise(date, rise=True):
    # lets return both time and azimuth since we are already computing it
    raleigh.date = date
    sun.compute(raleigh)
    if rise:
        raleigh.date = raleigh.next_rising(sun, date)
    else:
        raleigh.date = raleigh.next_setting(sun, date)
    sun.compute(raleigh)  # recompute to get azimuth at rise time
    return raleigh.date.datetime(), np.rad2deg(sun.az)


def sunset(date):
    # code reuse can also keep us out of trouble
    return sunrise(date, rise=False)


def sunlight(date):
    return ((sunset(date)[0] - sunrise(date)[0]).seconds) / 3600.0


def darkness(date):
    # look ahead ot the next sunrise
    return ((sunrise(date)[0] - sunset(date)[0]).seconds) / 3600.0


def builddf(start, end):
    df = pd.DataFrame(index=pd.date_range(start=start, end=end, freq='D'))
    df.index.name = 'date'

    df['sunrise'] = df.index.map(lambda d: sunrise(d)[0])  # sunrise time
    df['sunrise_az'] = df.index.map(lambda d: sunrise(d)[1])  # sunrise time
    df['sunset'] = df.index.map(lambda d: sunset(d)[0])  # sunset time
    df['sunset_az'] = df.index.map(lambda d: sunset(d)[1])  # sunset time
    df['hours of daylight'] = df.index.map(lambda d: sunlight(d))  # time the upper limb of the sun is above the horizon
    df['hours of darkness'] = df.index.map(lambda d: darkness(d))  # time the upper limb of the sun is below the horizon
    df['daylight delta'] = np.abs(df['hours of darkness'] - df['hours of daylight'])
    df['sunrise delta'] = np.abs(90.0 - df['sunrise_az'])
    df['sunset delta'] = np.abs(270.0 - df['sunset_az'])
    return df


def findmin(start, end, column):
    return _findminmax(start, end, column, findmin=True)


def findmax(start, end, column):
    return _findminmax(start, end, column, findmin=False)


def _findminmax(start, end, column, findmin=True):
    df = builddf(start, end)
    if findmin:
        result = df[column].idxmin()
    else:
        result = df[column].idxmax()
    return result


def closestto12hourssunlight(start, end):
    return findmin(start, end, 'daylight delta')


def sunriseclosesttodueeast(start, end):
    return findmin(start, end, 'sunrise delta')


def sunriseclosesttoduewest(start, end):
    return findmin(start, end, 'sunset delta')


class Test(unittest.TestCase):

    def test2017(self):
        result = builddf('2017-01-01 06:00', '2017-06-30')
        self.assertTrue(type(result['sunrise'][0]), datetime)
        self.assertTrue(type(result['sunrise_az'][0]), float)
        self.assertTrue(type(result['sunset'][0]), datetime)
        self.assertTrue(type(result['sunset_az'][0]), float)
        self.assertEqual(result.shape, (180, 9))

    def test2017closestto12hoursVernal(self):
        result = closestto12hourssunlight('2017-01-01', '2017-06-30')
        self.assertEqual(result.year, 2017)
        self.assertEqual(result.month, 3)

    def test2017closestto12hourswAutumnal(self):
        result = closestto12hourssunlight('2017-06-01', '2017-12-30')
        self.assertEqual(result.year, 2017)
        self.assertEqual(result.month, 9)

    def test2017closesttodueeastVernal(self):
        result = sunriseclosesttodueeast('2017-01-01', '2017-06-30')
        self.assertEqual(result.year, 2017)
        self.assertEqual(result.month, 3)


    def test2017closesttodueeastAutumnal(self):
        result = closestto12hourssunlight('2017-06-01', '2017-12-30')
        self.assertEqual(result.year, 2017)
        self.assertEqual(result.month, 9)


if __name__ == "__main__":
    year = 2021

    for data in [('winter-summer', f'{year}/01/01', f'{year}/06/30'), ('summer-winter', f'{year}-07-01', f'{year}-12-31')]:
        result = closestto12hourssunlight(data[1], data[2])
        print("\n%s (%s-%s)" % data)
        print('equinox:', ephem.localtime(ephem.next_equinox(data[1])))
        print("closest to equal daylight and darkness: %s %.4f hrs of daylight (%.4f hrs, %.2f sec)" % (
        # result['sunrise'].strftime('%D'), result['hours of daylight'], result['daylight delta'], result['daylight delta'] * 60 * 60))
        # result = sunriseclosesttodueeast(data[1], data[2])
        # print("closest to due east sunrise:            %s (%f degrees)" % (result['sunrise'].strftime('%D'), result['sunrise_az']))
        # result = sunriseclosesttoduewest(data[1], data[2])
        # print("closest to due west sunset:             %s (%f degrees)" % (result['sunset'].strftime('%D'), result['sunset_az']))
        # print()
