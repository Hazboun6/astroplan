from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

from ..constraints import (AltitudeConstraint, AirmassConstraint, AtNightConstraint,
                           is_observable, is_always_observable,
                           time_grid_from_range, SunSeparationConstraint)
from ..core import Observer, FixedTarget
import numpy as np
import astropy.units as u
from astropy.time import Time
from astropy.coordinates import SkyCoord, get_sun

vega = FixedTarget(coord=SkyCoord(ra=279.23473479*u.deg, dec=38.78368896*u.deg),
                   name="Vega")
rigel = FixedTarget(coord=SkyCoord(ra=78.63446707*u.deg, dec=8.20163837*u.deg),
                    name="Rigel")
polaris = FixedTarget(coord=SkyCoord(ra=37.95456067*u.deg,
                                     dec=89.26410897*u.deg), name="Polaris")

def test_at_night_basic():
    subaru = Observer.at_site("Subaru")
    time_ranges = [Time(['2001-02-03 04:05:06', '2001-02-04 04:05:06']), # 1 day
                   Time(['2007-08-09 10:11:12', '2007-08-09 11:11:12'])] # 1 hr
    targets = [vega, rigel, polaris]
    for time_range in time_ranges:
        # Calculate constraint using methods on astroplan.Observer:
        observer_is_night = [subaru.is_night(time)
                             for time in time_grid_from_range(time_range)]
        observer_is_night_any = any(observer_is_night)
        observer_is_night_all = all(observer_is_night)

        assert all(is_observable(AtNightConstraint(), time_range, targets, subaru) ==
                   len(targets)*[observer_is_night_any])

        assert all(is_always_observable(AtNightConstraint(), time_range, targets, subaru) ==
                   len(targets)*[observer_is_night_all])

def test_compare_altitude_constraint_and_observer():
    time = Time('2001-02-03 04:05:06')
    time_ranges = [Time([time, time+1*u.hour]) + offset
                   for offset in np.arange(0, 400, 100)*u.day]
    for time_range in time_ranges:
        subaru = Observer.at_site("Subaru")
        targets = [vega, rigel, polaris]

        min_alt = 40*u.deg
        max_alt = 80*u.deg
        # Check if each target meets altitude constraints using Observer
        always_from_observer = [all([min_alt < subaru.altaz(time, target).alt < max_alt
                                     for time in time_grid_from_range(time_range)])
                                for target in targets]
        # Check if each target meets altitude constraints using
        # is_always_observable and AltitudeConstraint
        always_from_constraint = is_always_observable(AltitudeConstraint(min_alt,
                                                                         max_alt),
                                                      time_range, targets, subaru)
        assert all(always_from_observer == always_from_constraint)

def test_compare_airmass_constraint_and_observer():
    time = Time('2001-02-03 04:05:06')
    time_ranges = [Time([time, time+1*u.hour]) + offset
                   for offset in np.arange(0, 400, 100)*u.day]
    for time_range in time_ranges:
        subaru = Observer.at_site("Subaru")
        targets = [vega, rigel, polaris]

        max_airmass = 2
        # Check if each target meets airmass constraint in using Observer
        always_from_observer = [all([subaru.altaz(time, target).secz < max_airmass
                                     for time in time_grid_from_range(time_range)])
                                for target in targets]
        # Check if each target meets altitude constraints using
        # is_always_observable and AirmassConstraint
        always_from_constraint = is_always_observable(AirmassConstraint(max_airmass),
                                                      time_range, targets, subaru)

        assert all(always_from_observer == always_from_constraint)

def test_sun_separation():
    time = Time('2003-04-05 06:07:08')
    apo = Observer.at_site("APO")
    sun = get_sun(time)
    one_deg_away = SkyCoord(ra=sun.ra, dec=sun.dec+1*u.deg)
    five_deg_away = SkyCoord(ra=sun.ra+5*u.deg, dec=sun.dec)
    twenty_deg_away = SkyCoord(ra=sun.ra+20*u.deg, dec=sun.dec)

    constraint = SunSeparationConstraint(min=2*u.deg, max=10*u.deg)
    is_constraint_met = constraint(time, apo, [one_deg_away,
                                               five_deg_away,
                                               twenty_deg_away])
    assert np.all(is_constraint_met == [[False], [True], [False]])
