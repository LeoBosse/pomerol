#!/usr/bin/python3
# -*-coding:utf-8 -*

import sys as sys
import numpy as np
import time as tm
import matplotlib.pyplot as plt
from matplotlib import cm
from matplotlib.patches import Circle
from matplotlib.patches import Ellipse
from matplotlib.patches import Arrow
# from matplotlib.lines import Line2D

import osgeo.gdal as gdal
gdal.UseExceptions()  # not required, but a good idea

import imageio

from observation import *
from rayleigh_utils import *
from sky_map import *
from ground_map import *
from atmosphere import *
from world import *
from input import *


class Simulation:
	def __init__(self, in_dict):
		"""Initialize the rayleigh object. It will be able to calculate a whole bunch of things!"""

		self.path = in_dict["path"]

		self.world = World(in_dict)

		self.save_individual_plots = bool(int(in_dict["saving_graphs"]))

		if not self.world.is_single_observation and self.world.is_time_dependant:
			print("Cannot compute several observation directions with a time changing sky. Please, my code is already messy enough as it is...")
			raise SystemExit

		list_shapes = (self.world.sky_map.Nt, len(self.world.e_pc_list), len(self.world.a_pc_list))
		### Initialize lists to save the final observable of each observation
		self.I_direct_list 	= np.zeros(list_shapes)
		self.I_list 	= np.zeros(list_shapes)
		self.IPola_list 	= np.zeros(list_shapes)
		self.InonPola_list 	= np.zeros(list_shapes)
		self.DoLP_list 	= np.zeros(list_shapes)
		self.AoRD_list = np.zeros(list_shapes)

		self.I_list_err = np.zeros(list_shapes)
		self.InonPola_list_err = np.zeros(list_shapes)
		self.IPola_list_err = np.zeros(list_shapes)
		self.DoLP_list_err = np.zeros(list_shapes)
		self.AoRD_list_err = np.zeros(list_shapes)

		print("Initialization DONE")


	def ComputeAllMaps(self):
		"""Will compute what the instrument sees for all the maps and all the observations directions"""

		if self.world.has_sky_emission: ### Compute how the sky maps looks through the instrument for every time and observations directions
			self.is_ground_emission = False
			for t in range(self.world.sky_map.Nt):
				# self.SetIMap(time = t)
				for ia_pc in range(self.world.Nb_a_pc):
					for ie_pc in range(self.world.Nb_e_pc):
						self.ia_pc, self.ie_pc = ia_pc, ie_pc
						self.world.a_pc, self.world.e_pc = self.world.a_pc_list[ia_pc], self.world.e_pc_list[ie_pc]
						self.a_pc, self.e_pc = self.world.a_pc, self.world.e_pc
						self.time = t
						self.SingleComputation()

			self.world.sky_map.SetLightParameters()

		if self.world.has_ground_emission: ### Compute how the ground map looks through the instrument for every observations directions
			self.is_ground_emission = True
			for ia_pc in range(self.world.Nb_a_pc):
				for ie_pc in range(self.world.Nb_e_pc):
					self.ia_pc, self.ie_pc = ia_pc, ie_pc
					self.world.a_pc, self.world.e_pc = self.world.a_pc_list[ia_pc], self.world.e_pc_list[ie_pc]
					self.a_pc, self.e_pc = self.world.a_pc, self.world.e_pc
					self.time = 0
					self.SingleComputation()

			self.world.ground_map.SetLightParameters()


		self.GetLightParametersList()

	def SingleComputation(self):
		"""Will compute and show what the instrument sees for one given I_map and one observation"""
		self.ComputeMaps()
		# self.MakePlots()

	def PrintSystematicResults(self):
		# mag = -2.5 * np.log10(self.I_list[0, 0, 0] * 10**-9 / (3.0128 * 10**28))
		# print("Magnitude", mag)

		print("t, a_pc, e_pc, src_dist (km), dlos (km), min_alt (km), max_alt (km), wavelength (nm), max_angle_discr (rad), I0, DoLP (%), AoRD (°), Direct I0:")
		for t in range(self.world.sky_map.Nt):
			for ie_pc in range(self.world.Nb_e_pc):
				for ia_pc in range(self.world.Nb_a_pc):
					print(t, self.world.a_pc_list[ia_pc]*RtoD, self.world.e_pc_list[ie_pc]*RtoD, self.world.ground_map.src_dist, self.world.atmosphere.d_los, self.world.atmosphere.h_r_min, self.world.atmosphere.h_r_max, self.world.wavelength, self.world.max_angle_discretization, self.I_list[t, ie_pc, ia_pc], self.DoLP_list[t, ie_pc, ia_pc], self.AoRD_list[t, ie_pc, ia_pc] * RtoD, self.I_direct_list[t, ie_pc, ia_pc], sep = "," )


	def GetLightParametersList(self):
		"""When the contributions of all maps for all times and all observations are done, compute the intensity, DoLP, AoLP lists.
		the lists have the shape: (time, e_pc, a_pc)"""
		for t in range(self.world.sky_map.Nt):
			for ie_pc in range(self.world.Nb_e_pc):
				for ia_pc in range(self.world.Nb_a_pc):
					self.GetLightParameters(ground = self.world.has_ground_emission, sky = self.world.has_sky_emission, time = t, ie_pc = ie_pc, ia_pc = ia_pc)

					self.I_list[t, ie_pc, ia_pc] = self.I0
					self.InonPola_list[t, ie_pc, ia_pc] = self.InonPola
					self.IPola_list[t, ie_pc, ia_pc] = self.I0 - self.InonPola
					self.DoLP_list[t, ie_pc, ia_pc] = self.DoLP
					self.AoRD_list[t, ie_pc, ia_pc] = self.AoRD

					# shutter_time = 60000 * 1000 #in milliseconds
					#
					# self.I_list_err[t, ie_pc, ia_pc] = np.sqrt(2 * self.I0 / shutter_time)
					# self.InonPola_list_err[t, ie_pc, ia_pc] = np.sqrt(2 * self.InonPola	/ shutter_time)
					# self.IPola_list_err[t, ie_pc, ia_pc] = np.sqrt(2 * self.IPola_list[t, ie_pc, ia_pc]	/ shutter_time)
					# self.DoLP_list_err[t, ie_pc, ia_pc] = np.sqrt(4 * (1 + ((self.DoLP/100.) ** 2 / 2)) / (self.I0 * shutter_time)) * 100
					# self.AoRD_list_err[t, ie_pc, ia_pc] = np.sqrt(1 / ((self.DoLP/100.)** 2 * self.I0 * shutter_time))


		# plt.plot(range(self.world.Nb_a_pc), self.InonPola_list[t, ie_pc, :])
		# plt.show()


	def SetSaveName(self):
		### Get the base name for the saving file -> unique for each parameter set
		self.save_name = "results/" + self.world.ground_map.location + "_" + self.world.sky_map.mode + "_a" + str(np.round(self.a_pc*RtoD, 0)) + "_e" + str(np.round(self.e_pc*RtoD, 0)) + "_h" + str(np.round(self.world.sky_map.h, 0)) + "_" + str(np.round(self.world.atmosphere.h_r_min, 0)) + "-" + str(np.round(self.world.atmosphere.h_r_max, 0)) + "_dlos" + str(np.round(self.world.atmosphere.d_los))

		if self.world.ground_map.radius > 0:
			self.save_name += "_D" + str(np.round(self.world.ground_map.radius * RT, 0))


	def ComputeMaps(self):
		"""Will initialize the last parameters that depend on the rest and will compute the contribution of each pixels from the map we set. We set the map by setting self.is_ground_emission to True or False. If False, then compute the sky map at the time set"""

		self.already_done = False
		if self.already_done:
			print("Observation already done. Loading old results from file", self.save_name)
		else:
			self.world.SetObservation(self.a_pc, self.e_pc)

			self.SetSaveName()
			print("*******************************************************************************************************************************")

			print("STARTING calculation for obs:")
			print(self.world.obs)

			if self.is_ground_emission == True:
				self.world.ComputeGroundMaps(self.time, self.ia_pc, self.ie_pc)
			else:
				self.world.ComputeSkyMaps(self.time, self.ia_pc, self.ie_pc)

		print("Computing DONE")

	def GetIDAFromV(self, V, Vc, Vs):
		I0 = 2 * V
		DoLP = 100 * 2 * np.sqrt(Vc**2 + Vs**2) / V
		AoLP = np.arctan2(Vs, Vc) / 2.

		return I0, DoLP, AoLP


	def GetLightParameters(self, ground = False, sky = False, time = None, ie_pc = None, ia_pc = None):
		"""Once the contributions of emmision maps are computed, compute the I, DOLP, AoLP and the AoLP histogram."""

		if time == None: time = self.time
		if ie_pc == None: ie_pc = self.ie_pc
		if ia_pc == None: ia_pc = self.ia_pc

		if sky and ground: #If sky and ground exist
			self.I_direct_list[time, ie_pc, ia_pc] = self.world.GetDirect(time, ia_pc, ie_pc)
			self.I0  = np.sum(self.world.sky_map.total_scattering_map[time, ie_pc, ia_pc].flatten())
			self.I0 += np.sum(self.world.ground_map.total_scattering_map[ie_pc, ia_pc].flatten())
			# self.I0 += self.I_direct_list[time, ie_pc, ia_pc]
			self.InonPola = self.I0 - np.sum(self.world.ground_map.scattering_map[ie_pc, ia_pc].flatten()) - np.sum(self.world.sky_map.scattering_map[time, ie_pc, ia_pc].flatten())
		elif ground: #If sky doesn't exist
			self.I0 = np.sum(self.world.ground_map.total_scattering_map[ie_pc, ia_pc].flatten())
			self.InonPola = self.I0 - np.sum(self.world.ground_map.scattering_map[ie_pc, ia_pc].flatten())
			print(self.I0, self.InonPola)
		elif sky:  #If ground doesn't exist
			self.I_direct_list[time, ie_pc, ia_pc] = self.world.GetDirect(time, ia_pc, ie_pc)
			self.I0  = np.sum(self.world.sky_map.total_scattering_map[time, ie_pc, ia_pc].flatten())
			# self.I0 += self.I_direct_list[time, ie_pc, ia_pc]
			self.InonPola = self.I0 - np.sum(self.world.sky_map.scattering_map[time, ie_pc, ia_pc].flatten())

		tmp_start = tm.time()
		if False:
			self.DoLP = self.world.ground_map.DoLP_map[ie_pc, ia_pc, 0, 0] * 100 # / self.I0 * 100
			# self.DoLP = np.sum(self.world.ground_map.scattering_map[time, ie_pc, ia_pc].flatten()) / self.I0 * 100
			self.AoRD = self.world.ground_map.AoRD_map[ie_pc, ia_pc, 0, 0] * RtoD
		elif True:

			self.V, self.Vcos, self.Vsin = 0, 0, 0
			if ground: #If ground and ground exist
				self.V 		+= self.world.ground_map.V_total[ie_pc, ia_pc]
				self.Vcos 	+= self.world.ground_map.Vcos_total[ie_pc, ia_pc]
				self.Vsin 	+= self.world.ground_map.Vsin_total[ie_pc, ia_pc]
			if sky: #If sky and ground exist
				self.V 		+= self.world.sky_map.V_total[time, ie_pc, ia_pc]
				self.Vcos 	+= self.world.sky_map.Vcos_total[time, ie_pc, ia_pc]
				self.Vsin 	+= self.world.sky_map.Vsin_total[time, ie_pc, ia_pc]

			self.I0, self.DoLP, self.AoRD = self.GetIDAFromV(self.V, self.Vcos, self.Vsin)
			self.IPola = self.I0 * self.DoLP / 100.
			self.InonPola = self.I0 - self.IPola

			# hst, bins = np.zeros(self.N_bins), np.zeros(self.N_bins)
			if sky:
				A = self.world.sky_map.AoRD_map[time, ie_pc, ia_pc, :, :]
				Ip = self.world.sky_map.scattering_map[time, ie_pc, ia_pc, :, :]

				sky_hst, self.bins = self.world.MakeAoRDHist(A, Ipola = Ip)

			if ground:
				A = self.world.ground_map.AoRD_map[ie_pc, ia_pc, :, :]
				Ip = self.world.ground_map.scattering_map[ie_pc, ia_pc, :, :]
				ground_hst, self.bins = self.world.MakeAoRDHist(A, Ipola = Ip)

			if sky:
				self.hst = sky_hst
				if ground:
					self.hst += ground_hst
			elif ground:
				self.hst = ground_hst

			# self.V, self.Vcos, self.Vsin, self.I0, self.DoLP, self.AoRD = self.world.LockInAmplifier(self.hst, self.bins, self.InonPola)

			if self.world.is_single_observation:
				self.world.DrawAoLPHist(self.hst,self.bins, self.I0, self.DoLP, self.AoRD, double=True, save = self.save_individual_plots, save_name = self.path + self.save_name + '_hist.png', show=True)

		return self.I0, self.DoLP, self.AoRD


	def MakePlots(self):
		################################################################################
		###	PLOTTING
		################################################################################

		################################################################################
		###	Polar plots of intensity

		font = {'family' : 'DejaVu Sans',
		'weight' : 'bold',
		'size'   : 24}
		matplotlib.rc('font', **font)

		if self.save_individual_plots:
			print("Making and saving plots...")
		else:
			print("Making and NOT saving plots...")

		if self.is_ground_emission:
			self.MakeGroundMapPlots()
		else:
			self.MakeSkyMapPlots()

		# self.MakeAoLPHist(ground = self.is_ground_emission, sky = not self.is_ground_emission, double=True)
		# if self.world.is_single_observation:
		self.world.DrawAoLPHist(self.hst,self.bins, self.I0, self.DoLP, self.AoRD, double=True, save = self.save_individual_plots, save_name = self.path + self.save_name + '_hist.png', show=False)

		self.MakeAoLPMap()

		# if self.world.is_single_observation and not self.world.is_time_dependant:
		# 	plt.show()

		# plt.close("all")


	def MakeSkyMapPlots(self):
		"""Make plots of the sky emission map contributions. Plot the initial intensity, the scattered intensity, the DOLP..."""
		f1, (ax1, ax2, ax3, ax4) = plt.subplots(4, sharex = True, sharey = True, figsize=(16, 8))
		ax1 = plt.subplot(221, projection='polar')
		ax2 = plt.subplot(222, projection='polar')
		ax3 = plt.subplot(223, projection='polar')
		ax4 = plt.subplot(224, projection='polar')

		# So that e = 90 is in the center of the plot if the emission layer is NOT the ground
		el = 90 - (self.world.sky_map.elevations[:]) * RtoD
		# i1 = ax1.pcolormesh(azimuts, el, scattering_map)
		i1 = ax1.pcolormesh(self.world.sky_map.azimuts[:], el, self.world.sky_map.cube[self.time, :, :])
		i2 = ax2.pcolormesh(self.world.sky_map.azimuts[:], el, self.world.sky_map.total_scattering_map[self.time, self.ie_pc, self.ia_pc, :, :])
		i3 = ax3.pcolormesh(self.world.sky_map.azimuts[:], el, self.world.sky_map.scattering_map[self.time, self.ie_pc, self.ia_pc, :, :])
		# i4 = ax4.pcolormesh(azimuts, el, total_scattering_map)
		i4 = ax4.pcolormesh(self.world.sky_map.azimuts[:], el, self.world.sky_map.AoRD_map[self.time, self.ie_pc, self.ia_pc, :, :]*RtoD, cmap=cm.twilight)

		cbar1 = f1.colorbar(i1, extend='both', spacing='proportional', shrink=0.9, ax=ax1)
		cbar1.set_label('Initial emission map')
		cbar2 = f1.colorbar(i2, extend='both', spacing='proportional', shrink=0.9, ax=ax2)
		cbar2.set_label('Total intensity map')
		cbar3 = f1.colorbar(i3, extend='both', spacing='proportional', shrink=0.9, ax=ax3)
		cbar3.set_label('Polarised intensity map')
		cbar4 = f1.colorbar(i4, extend='both', spacing='proportional', shrink=0.9, ax=ax4)
		cbar4.set_label('AoRD')

		f1.suptitle("Relevant angles map at skibotn, with light pollution source at -45deg in azimut")

		for a in [ax1, ax2, ax3, ax4]:
			a.set_theta_zero_location("N")
			a.set_theta_direction(-1)
			a.set_thetamin(self.world.sky_map.I_zone_a_min * RtoD)
			a.set_thetamax(self.world.sky_map.I_zone_a_max * RtoD)

			a.set_rlim(0,90, 1)
			a.set_yticks(np.arange(0, 90, 20))
			a.set_yticklabels(a.get_yticks()[::-1])   # Change the labels

			a.add_artist(Ellipse((self.a_pc, 90 - self.e_pc * RtoD), width=self.world.ouv_pc, height=self.world.ouv_pc*RtoD, color="red"))

		if self.save_individual_plots:
			plt.savefig(self.path + self.save_name + '_skymaps.png', bbox_inches='tight')

	def MakeGroundMapPlots(self):
		"""Make plots of the ground emission map contributions. Plot the initial intensity, the scattered intensity, the DOLP..."""
		f2, (ax1, ax2, ax3, ax4) = plt.subplots(4, sharex = True, sharey = True, figsize=(16, 8))
		ax1 = plt.subplot(221)
		ax2 = plt.subplot(222)
		ax3 = plt.subplot(223)
		ax4 = plt.subplot(224)

		i1 = ax1.pcolormesh((self.world.ground_map.longitudes-self.world.ground_map.A_lon) * RT, (self.world.ground_map.latitudes-self.world.ground_map.A_lat) * RT, self.world.ground_map.I_map)
		i2 = ax2.pcolormesh((self.world.ground_map.longitudes-self.world.ground_map.A_lon) * RT, (self.world.ground_map.latitudes-self.world.ground_map.A_lat) * RT, self.world.ground_map.total_scattering_map[self.ie_pc, self.ia_pc, :, :])		# Intensity from (e, a) reaching us
		i3 = ax3.pcolormesh((self.world.ground_map.longitudes-self.world.ground_map.A_lon) * RT, (self.world.ground_map.latitudes-self.world.ground_map.A_lat) * RT, self.world.ground_map.scattering_map[self.ie_pc, self.ia_pc, :, :])				# Polarized intensity from (e, a) reaching us
		i4 = ax4.pcolormesh((self.world.ground_map.longitudes-self.world.ground_map.A_lon) * RT, (self.world.ground_map.latitudes-self.world.ground_map.A_lat) * RT, self.world.ground_map.DoLP_map[self.ie_pc, self.ia_pc, :, :])	# DoLP of scattered light from (e,a)
		# i4 = ax4.pcolormesh((longitudes-A_lon) * RT, (latitudes-A_lat) * RT, AoRD_map * RtoD, cmap=cm.twilight)			# AoLP of scattered light from (e,a)


	# Angle of polaisation of light from (e,a)
		cbar1 = f2.colorbar(i1, extend='both', spacing='proportional', shrink=0.9, ax=ax1)
		cbar1.set_label('Initial emission map')
		cbar2 = f2.colorbar(i2, extend='both', spacing='proportional', shrink=0.9, ax=ax2)
		cbar2.set_label('Total intensity map')
		cbar3 = f2.colorbar(i3, extend='both', spacing='proportional', shrink=0.9, ax=ax3)
		cbar3.set_label('Polarised intensity map')
		cbar4 = f2.colorbar(i4, extend='both', spacing='proportional', shrink=0.9, ax=ax4)
		cbar4.set_label('DoLP')

		f2.suptitle("Relevant angles map at skibotn, with light pollution source at -45deg in azimut")

		dy = np.cos(self.a_pc) * self.world.atmosphere.h_r_max / np.tan(self.e_pc)
		dx = np.sin(self.a_pc) * self.world.atmosphere.h_r_max / np.tan(self.e_pc)
		for a in [ax1, ax2, ax3, ax4]:
			a.add_artist(Arrow(0, 0, dx, dy, color="red"))

		if self.save_individual_plots:
			plt.savefig(self.path + self.save_name + '_groundmaps.png', bbox_inches='tight')



	def MakeAoLPMap(self):
		"""Make a pyplot quiver of the AoLP contribution of each emission point. Vertical means AoLP=0, horyzontal AoLP = 90.
		Need a call to plt.show() after calling this function."""
		f4, (ax1) = plt.subplots(1, sharex=True, figsize=(16, 8))



		if not self.is_ground_emission:
			ax1.set_xlabel("Azimuts")
			ax1.set_ylabel("Elevations")
			X, Y = self.world.sky_map.mid_azimuts * RtoD, self.world.sky_map.mid_elevations * RtoD
			U, V = np.sin(self.world.sky_map.AoRD_map[self.time, self.ie_pc, self.ia_pc, :, :]) * self.world.sky_map.DoLP_map[self.time, self.ie_pc, self.ia_pc, :, :], np.cos(self.world.sky_map.AoRD_map[self.time, self.ie_pc, self.ia_pc, :, :]) * self.world.sky_map.DoLP_map[self.time, self.ie_pc, self.ia_pc, :, :]
			M = self.world.sky_map.DoLP_map[self.time, self.ie_pc, self.ia_pc, :, :]
		else:
			ax1.set_xlabel("Longitudes")
			ax1.set_ylabel("Latitudes")
			X, Y = self.world.ground_map.mid_longitudes * RtoD, self.world.ground_map.mid_latitudes * RtoD
			U, V = np.sin(self.world.ground_map.AoRD_map[self.ie_pc, self.ia_pc, :, :]) * self.world.ground_map.DoLP_map[self.ie_pc, self.ia_pc, :, :], np.cos(self.world.ground_map.AoRD_map[self.ie_pc, self.ia_pc, :, :]) * self.world.ground_map.DoLP_map[self.ie_pc, self.ia_pc, :, :]
			M = self.world.ground_map.DoLP_map[self.ie_pc, self.ia_pc, :, :]


		q = ax1.quiver(X, Y, U, V, M, pivot="middle", headwidth=0, headlength=0, headaxislength=0)
		ax1.quiverkey(q, 0.5, 1.1, 1, "AoRD")
		if not self.is_ground_emission:
			ax1.add_artist(Circle((self.a_pc * RtoD, self.e_pc * RtoD), radius=self.world.ouv_pc * RtoD, color="red"))

		if self.save_individual_plots:
			plt.savefig(self.path + self.save_name + '_AoRD_map.png', bbox_inches='tight')

		################################################################################
		###	AoRD map as stream plot (continuous lines)
	# def MakeAoLPStram(self):
		# f5, (ax1) = plt.subplots(1, sharex=True, figsize=(16, 8))
		#
		# ax1.set_xlabel("Azimuts")
		# ax1.set_ylabel("Elevations")
		#
		# if h != 0: 	X, Y = azimuts * RtoD, elevations * RtoD
		# else:		X, Y = longitudes * RtoD, latitudes * RtoD
		# U, V = np.sin(AoRD_map) * DoLP_map, np.cos(AoRD_map) * DoLP_map
		# M = DoLP_map
		#
		# ax1.streamplot(X, Y, U, V, color=M, density=2, arrowstyle="-")
		# if h != 0: 	ax1.add_artist(Circle((a_pc * RtoD, e_pc * RtoD), radius=ouv_pc * RtoD, color="red"))

		# np.savetxt(self.path + self.save_name + "_scattering_map.cvs", self.scattering_map)
		# np.savetxt(self.path + self.save_name + "_DoLP_map.cvs", self.DoLP_map)
		# np.savetxt(self.path + self.save_name + "_total_scattering_map.cvs", self.total_scattering_map)
		# np.savetxt(self.path + self.save_name + "_AoRD_map.cvs", self.AoRD_map)


	def MakeSummaryPlot(self):

		# print("Azimut, Elevation, I, DoLP, AoLP")
		# for t in range(self.world.sky_map.Nt):
		# 	for ia, a in enumerate(self.a_pc_list):
		# 		for ie, e in enumerate(self.e_pc_list):
		# 			print(a*RtoD, e*RtoD, self.I_list[t][ie][ia], self.DoLP_list[t][ie][ia], self.AoRD_list[t][ie][ia]*RtoD)

		font = {'family' : 'DejaVu Sans',
		'weight' : 'bold',
		'size'   : 24}
		matplotlib.rc('font', **font)

		if not self.world.is_time_dependant:
			if self.world.is_single_observation:
				# self.MakeAoLPHist(ground = self.world.has_ground_emission, sky = self.world.has_sky_emission)
				self.MakePlots()
				# pass
			else:
				f, axs = plt.subplots(3, sharex = True, figsize=(16, 8))
				axs[0] = plt.subplot(311)
				axs[1] = plt.subplot(312)
				axs[2] = plt.subplot(313)

				if self.world.Nb_e_pc > 1 and self.world.Nb_a_pc > 1:
					axs[0].imshow(self.I_list[0,:,:])
					axs[1].imshow(self.DoLP_list[0,:,:])
					axs[2].imshow(self.AoRD_list[0,:,:]*RtoD)
					self.save_name = 'results/' + self.world.ground_map.location + "_skymap" + ".png"
				else:
					if self.world.Nb_e_pc == 1:
						xaxis = self.world.a_pc_list*RtoD
						I = self.I_list[0, 0, :]
						Ierr = self.I_list_err[0, 0, :] / 2.
						InonPola = self.InonPola_list[0, 0, :]
						InonPolaerr = self.InonPola_list_err[0, 0, :] / 2.
						IPola = self.IPola_list[0, 0, :]
						IPolaerr = self.IPola_list_err[0, 0, :] / 2.
						D = self.DoLP_list[0, 0, :]
						Derr = self.DoLP_list_err[0, 0, :] / 2.
						A = self.AoRD_list[0, 0, :] * RtoD
						Aerr = self.AoRD_list_err[0, 0, :] / 2. * RtoD
						self.save_name = 'results/' + self.world.ground_map.location + "_rot_e" + str(self.world.e_pc_list[0]*RtoD) + ".png"

						print(I - Ierr)

					elif self.world.Nb_a_pc == 1:
						xaxis = self.world.e_pc_list*RtoD
						I = self.I_list[0, :, 0]
						Ierr = self.I_list_err[0, :, 0] / 2.
						InonPola = self.InonPola_list[0, :, 0]
						InonPolaerr = self.InonPola_list_err[0, :, 0] / 2.
						IPola = self.IPola_list[0, :, 0]
						IPolaerr = self.IPola_list_err[0, :, 0] / 2.
						D = self.DoLP_list[0, :, 0]
						Derr = self.DoLP_list_err[0, :, 0] / 2.
						A = self.I_list[0, :, 0]
						Aerr = self.I_list_err[0, :, 0] / 2.
						self.save_name = 'results/' + self.world.ground_map.location + "_rot_a" + str(self.world.a_pc_list[0]*RtoD) + ".png"

					axs[0].plot(xaxis, I, label = "All")
					axs[0].fill_between(xaxis, I - Ierr, I + Ierr, alpha = 0.2)

					axs[0].plot(xaxis, InonPola, "r", label = "Non polarized")
					axs[0].fill_between(xaxis, InonPola - InonPolaerr, InonPola + InonPolaerr, alpha = 0.2)

					axs[0].plot(xaxis, IPola, "g", label = "Polarized")
					axs[0].fill_between(xaxis, IPola - IPolaerr, IPola + IPolaerr, alpha = 0.2)

					axs[1].plot(xaxis, D)
					axs[1].fill_between(xaxis, D - Derr, D + Derr, alpha = 0.2)

					axs[2].plot(xaxis, A)
					axs[2].fill_between(xaxis, A - Aerr, A + Aerr, alpha = 0.2)

				axs[0].set_ylabel("Intensity (nW)")
				axs[1].set_ylabel("DoLP (\%)")
				axs[2].set_ylabel("AoLP (°)")
		else:
			f, axs = plt.subplots(3, sharex = True, figsize=(16, 8))
			axs[0] = plt.subplot(311)
			axs[1] = plt.subplot(312)
			axs[2] = plt.subplot(313)
			axs[0].set_ylabel("Intensity (nW)")
			axs[1].set_ylabel("DoLP, (\%)")
			axs[2].set_ylabel("AoLP (°)")

			self.world.sky_map.MakeSkyCubePlot(self.world.a_pc_list, self.world.e_pc_list, self.world.ouv_pc)
			axs[0].set_yscale('log')
			# axs[0].plot(range(self.world.sky_map.Nt), (self.I_list[:, 0, 0] / (self.I_direct_list[:, 0, 0] + self.I_list[:, 0, 0])).tolist())
			# print(self.I_list[:, 0, 0].tolist())
			# print(self.I_direct_list[:, 0, 0].tolist())
			axs[0].plot(range(self.world.sky_map.Nt), self.I_list[:, 0, 0].tolist())
			# axs[0].plot(range(self.world.sky_map.Nt), self.I_direct_list[:, 0, 0].tolist())
			axs[1].plot(range(self.world.sky_map.Nt), self.DoLP_list[:, 0, 0].tolist())
			axs[2].plot(range(self.world.sky_map.Nt), (self.AoRD_list[:, 0, 0]*RtoD).tolist())
			self.save_name = 'results/' + self.world.ground_map.location + "_" + self.world.sky_map.mode + "_time_series_a" + str(self.world.a_pc_list[0]*RtoD) + "_e" + str(self.world.e_pc_list[0]*RtoD) + ".png"

		# plt.savefig(self.path + self.save_name, bbox_inches='tight')
