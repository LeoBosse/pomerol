#!/usr/bin/python3
# -*-coding:utf-8 -*

import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt
import sys
import os
from subprocess import call
import datetime as dt

# import radis
import astropy.io.fits as fits
import astropy.units as u
from astropy.coordinates import AltAz, EarthLocation, SkyCoord, get_sun, get_body
from astropy.time import Time

from pybaselines import Baseline, utils
import argparse

from spec_utils import *


from MagData import *



### Read the command line arguments. And store them in a dictionnary called args.
parser = argparse.ArgumentParser()
parser.add_argument('-f', '--datafile', help='The data file to analyse. Relative path to /home/leob/iasb/analysis/data/skibotn_spectro/' )
args = parser.parse_args()


# file_name = 'data_100um_30sec_Sun Oct 8 2023_04.47.44_73.fits'
# file_name = 'data_30sec_100um_Mon Oct 9 2023_07.31.06_75.fits'
file_name = args.datafile #'data_G1_30sec_100um_Tue Oct 10 2023_04.48.32_76.fits'


dark_file_30 = Serie.path + 'darks/240x30sec_G1_FVB_Sat Oct 7 2023_15.56.51_37.fits'
dark_file_60 = Serie.path + 'darks/90x1min_G1_FVB_Sat Oct 7 2023_13.32.24_36.fits'

serie = Serie.FromFitsFile(Serie.path + file_name)
# serie.MaskSunMoon(sun_limit = -12)

print(serie)

serie.SetDark(dark_file_30, dark_file_60)
serie.SubtractDarks()
# serie.data = serie.data - serie.darks

serie.SetBaseLines(algo='asls')
serie.SubtractBaseLines()


# serie.data = serie.data - serie.baselines


# serie.GetCosmics()
# print(np.where(serie.cosmics[159]))

# serie.SetGradient()

# serie.MakeSpectrumFigure(serie.nb_spec//2)

# serie.RemoveCosmicRays('dd')
serie.MakeSpectrumFigure(143)
print(serie.GetMax())

# data_mp= serie.RemoveCosmicRays('mp')
# data_med = serie.RemoveCosmicRays('med')
# serie.MakeSpectrumFigure(159, data_dd)
# serie.MakeSpectrumFigure(159, data_mp)
# serie.MakeSpectrumFigure(159, data_med)

# n = 0
# for i in range(serie.nb_spec):
#     if n < 10 and np.any(serie.cosmics[i]):
#         serie.MakeSpectrumFigure(i)
#         n += 1


### Load the magnetometer data
mag_data = MagData.FromSpectroSerie(serie)
if mag_data.exist:
    mag_data.MakeFigure()


### Plot Spectrum
serie.PlotImage()
serie.Plot3D()
serie.MakeAnimation()

### Combine spectra
start, end = 400, 1123 #0, 1400
fct = np.sum

comb_spectrum = serie.CombineSpectra(start, end, fct)
comb_spectrum = Spectrum(serie.spectra[start].header, comb_spectrum)
comb_spectrum.MakeFigure()


# ### Add auroral lines
# serie.AddLine(557.7, 1.5, color = 'g')
# serie.AddLine(629.5, 2,   color = 'r', delay = 0)
# serie.AddLine(424,   5,   color = 'b', delay = 0)


serie.AddLine(485.5, 2.5,   color = 'b', delay = 0)
serie.AddLine(655,   3,     color = 'r', delay = 0)


# serie.AddLine(520,   2,   color = 'orange', delay = 0) #35820.0sec = 9.95h
# serie.AddLine(465,   3  , delay = 0)
# serie.AddLine(470.5, 4  , delay = 0)
# serie.AddLine(500.5, 3  , delay = 0)
# serie.AddLine(523. , 4  , delay = 0)
# serie.AddLine(526.5, 4  , delay = 0)
# serie.AddLine(568.5, 4  , delay = 0)
# serie.AddLine(589. , 6  , delay = 0)
# serie.AddLine(600. , 6  , delay = 0)
# serie.AddLine(613. , 6  , delay = 0)
# serie.AddLine(645.5, 6  , delay = 0)
# serie.AddLine(652.5, 6  , delay = 0)
# serie.AddLine(660.5, 6  , delay = 0)
# serie.AddLine(668.5, 6  , delay = 0)
# serie.AddLine(676.5, 6  , delay = 0)

for l in serie.lines:
    l.GetIntegral()
    # l.PlotImage()
    # l.Plot3D()

fig = plt.figure()
fig.suptitle("Line power")
for l in serie.lines:
    plt.plot(serie.times - l.delay, l.integral, l.color)
    plt.plot(serie.times, l.integral, '--', color = l.color)
    
fig = plt.figure()
fig.suptitle("Line ratios")
ax = fig.add_subplot(111)
for l in serie.lines[1:]:
    ratio = l.GetRatio(serie.lines[0])
    ax.plot(l.times[:len(ratio)] - l.delay, ratio, l.color)
# if mag_data.exist:
#     ax.twinx().plot(mag_data.datetime, mag_data.Horiz, '--k')

# ratio = serie.lines[1].GetRatio(serie.lines[2])
# ax.plot(serie.lines[1].times[:len(ratio)] - serie.lines[1].delay, ratio, "purple")


# plt.figure()
# for i, l0 in enumerate(serie.lines):
#     for l1 in serie.lines[i+1:]:
#         for it in range(len(serie.times)):
#             if l0.integral[it] > 200 and l1.integral[it] > 200:
#                 plt.plot(l0.integral[it] / np.max(l0.integral), l1.integral[it] / np.max(l1.integral), '.')
         


plt.legend()
plt.show()
