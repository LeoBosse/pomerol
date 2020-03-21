#!/usr/bin/python3
# -*-coding:utf-8 -*


import mysql.connector as mysql
import sys
import os.path
import numpy as np

class Input:
	def __init__(self, input_file = ""):
		self.template = "/home/bossel/These/Analysis/src/input_files/template.in"

		if not input_file:
			input_file = self.template

		self.dictionnary, self.comments = self.ReadInputFile(input_file)

	def Update(self, dict):
		for key, value in dict.items():
			if key == "observation_type":
				self.SetObservationType(value)
			else:
				self.dictionnary[key] = value


	def SetPollutionSource(self, lieu = "", az = 0, el = 0):
		if lieu.lower() == "skibotn":
			az, el = -45, 0
		elif lieu.lower() == "nyalesund":
			az, el = 1, 0
		elif lieu.lower() == "corbel":
			az, el = -60, 0

		self.dictionnary["pollution_source_azimut"] = az
		self.dictionnary["pollution_source_elevation"] = el


	def SetObservationType(self, new_type, el = 0):
		old_type = self.dictionnary["observation_type"]
		if new_type == old_type:
			return True

		self.dictionnary["observation_type"] = new_type

		if new_type == "fixed_elevation_continue_rotation":
			self.dictionnary["continue_rotation_elevation"] = self.dictionnary.pop("#continue_rotation_elevation")
			self.dictionnary["continue_rotation_times"] = self.dictionnary.pop("#continue_rotation_times")
			if el != 0:
				self.dictionnary["continue_rotation_elevation"] = el
			if old_type == "fixed_elevation_discrete_rotation":
				self.dictionnary["#discrete_rotation_azimut"] = self.dictionnary.pop("discrete_rotation_azimut")
				self.dictionnary["#discrete_rotation_times"] = self.dictionnary.pop("discrete_rotation_times")
				self.dictionnary["#discrete_rotation_elevations"] = self.dictionnary.pop("discrete_rotation_elevations")

		elif new_type == "fixed_elevation_discrete_rotation":
			self.dictionnary["discrete_rotation_azimut"] = self.dictionnary.pop("#discrete_rotation_azimut")
			self.dictionnary["discrete_rotation_times"] = self.dictionnary.pop("#discrete_rotation_times")
			self.dictionnary["discrete_rotation_elevations"] = self.dictionnary.pop("#discrete_rotation_elevations")

			if old_type == "fixed_elevation_continue_rotation":
				self.dictionnary["#continue_rotation_elevation"] = self.dictionnary.pop("continue_rotation_elevation")
				self.dictionnary["#continue_rotation_times"] = self.dictionnary.pop("continue_rotation_times")

		elif new_type == "fixed":
			if old_type == "fixed_elevation_continue_rotation":
				self.dictionnary["#continue_rotation_elevation"] = self.dictionnary.pop("continue_rotation_elevation")
				self.dictionnary["#continue_rotation_times"] = self.dictionnary.pop("continue_rotation_times")
			if old_type == "fixed_elevation_discrete_rotation":
				self.dictionnary["#discrete_rotation_azimut"] = self.dictionnary.pop("discrete_rotation_azimut")
				self.dictionnary["#discrete_rotation_times"] = self.dictionnary.pop("discrete_rotation_times")
				self.dictionnary["#discrete_rotation_elevations"] = self.dictionnary.pop("discrete_rotation_elevations")



	def ReadInputFile(self, file_name):
		"""Read a given input file and return a dictionnary. First word = key, second = value. Remove empty lines, as many arguments as you want, in any order that you want."""
		with open(file_name, "r") as f: #open the file
			input = f.readlines() #store all lines in input

		input = [l.split()[:] for l in input if l != "\n"] #get first two words (separated by a space) for all non empty line

		dict = {i[0]: i[1] for i in input} #Create dictionnary
		comments = {i[0]: " ".join(i[2:]) for i in input if len(i) > 2}

		return dict, comments

	def WriteInputFile(self, folder, file_name = "/input.in"):
		with open(folder + file_name, "w") as f_in:
			for key, value in self.dictionnary.items():
				f_in.write(" ".join((key, str(value))))
				if self.comments.__contains__(key):
					f_in.write(comments[key])
				f_in.write("\n")
