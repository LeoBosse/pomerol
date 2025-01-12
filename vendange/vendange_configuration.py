#!/usr/bin/python3
# -*-coding:utf-8 -*

from pathlib import Path


class Config:
	"""
	class to store all general configuration parameters of the software. Mainly to store all the paths and folder names in one place.
	"""

	def __init__(self):
		# Common denominator path. THe path shared by all data and source folders
		
		self.path 						= Path(__file__).resolve().parent.parent.parent
		# self.path 						= "/home/leob/iasb/analysis/"

		self.data_path 					= self.path / "data" # Folder where all your data are stored.
		self.src_path 					= self.path / "src" / "vendange" # Folder where all your source files are stored (this file is in this folder).

		self.input_path 				= self.src_path  / "input_files" # Folder where all your input files are stored..
		self.allsky_data_path 			= self.data_path / "allsky_camera" / "tid.uio.no" / "plasma" / "aurora" #Path for all_sky camera pictures. It follows the automatic path scheme of the website.
		self.magnetometer_data_path	 	= self.data_path / "magnetometer" # Path for all magnetometer data
		self.eiscat_data_path 			= self.data_path / "eiscat" # Path for EISCAT data
		self.plip_data_path 			= self.data_path / "plip" # Path for PLIP data
		self.eq_current_data_path 		= self.data_path / "equivalent_currents" # Path for equivalent current data
		self.chaos_model_file 			= self.data_path / "magn_field" / "CHAOS-7.4.mat" # Path for the chaos model file		self.input_path					= self.src_path + "input_files/" # Path where input files can be stored and where the templates are.

### Making a Config() object to be used throughout the code.
global_configuration = Config()
