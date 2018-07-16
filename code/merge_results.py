from utils import *
from parse_ads_txt_location import *
import re
import pandas as pd
from check_url import *
import os
import os.path
import numpy as np


'''
After checking the URLs for validity of a text file, we want to take the information 
and process it into our giant text file. Tentatively thinking that this set of functions
will rely upon a dictionary from ad_text_url to ad_text_url_content.

Need to figure out how to merge results into whatever text/csv file we have. 

'''

#output file where we will make changes
output_file_name = '../generated_apps_info.txt'



def process_scan_results(scan_results, domains_that_404, untracked_supply_vendor_domains):
	'''
	scan_results is a dictionary from domain name to value of domain
	domains_that_404 is a list of domains that used to have an ads.txt file but no longer do (returned 404)
	untracked_supply_vendor_domain are domains that we see in ads.txt files that aren't updated yet (not sure if this will be
	relevant sine we no longer maintain a DB and use a public text/csv file)

	Function takes all the crawl results that we receive, and creates a list of adds, mods, and deletes we need to do to update our file

	'''
	pass

def create_change_list(app_ids_to_urls_dict):

	'''
	apps_ids_to_urls_dict is a dictionary from app id to the list of possible locations for ads.txt
	This function goes through and checks if there's an ads.txt file. If there is, it will save it to a list 
	and then process it later into the text file.	
	returns a list of changes 
	'''
	change_set = []

	for app_id in apps_ids_to_urls_dict:
		app_id_ads_txt_locations = []
		for url in apps_ids_to_urls_dict[app_id]:
			if check_valid_url_ad_text(url):
				app_id_ads_txt_locations.append(url)

		if not app_id_ads_txt_locations: #no valid url
			change_set.append((app_id, 'NONE')) #NONE is just a marker telling us that there is no ads.txt file
		else: #we found at least one valid location for ads.txt
			tuple_form_locations = tuple(app_id_ads_txt_locations)
			change_set.append((app_id, tuple_form_locations))

	return change_set



def merge_into_file(file_name, list_of_changes):
	'''
	file_name: output file location
	list_of_changes: list of changes generated by process_scan_results that we will step through and make in the file
		Structured as:
			[(app id, urls or NONE), ..]
		
	'''

	def check_existing_app_id(app_id_name, dataframe):
		'''
		Checks if the csv file already contains the current app_id
		'''
		exists = (dataframe.index == app_id_name).any()
		if exists:
			print(app_id_name + " already exists in csv file. Updating...")
		else:
			print(app_id_name + " is a new entry. Adding...")
		return exists


	def modify_existing_csv():
		'''
		there's already a csv file present so we just need to update it.
		'''
		csv_dataframe = pd.read_csv(file_name)

		new_app_ids_list = []

		for change in list_of_changes:
			current_app_id, ads_txt_location = change

			if ads_txt_location == 'NONE':
				ads_txt_location = 'No ads.txt found.'

			if check_existing_app_id(current_app_id, csv_dataframe): #app id already exists, so we have to update that row 

				#looks for existing row and updates ads.txt location
				csv_dataframe.loc[csv_dataframe['app_id'] == current_app_id, 'ads.txt_location'] = ads_txt_location
				
			else: #adding a new entry to csv table
				new_app_ids_list.append()

		new_entries_dataframe = create_new_csv(new_app_ids_list)
		csv_dataframe.append(new_entries_dataframe)

		return csv_dataframe


	def create_new_csv(changes):
		'''
		No csv file so we have to create it from current info.
		'''
		def convert_to_array():
			app_id_ads_txt_array = np.empty((2, len(changes)))
			for change in range(len(changes)):
				current_app_id, ads_txt_location = changes[change]
				if ads_txt_location == 'NONE':
					ads_txt_location = 'No ads.txt found.'
				app_id_ads_txt_array[0][change] = current_app_id
				app_id_ads_txt_array[1][change] = ads_txt_location
			return app_id_ads_txt_array


		column_names = ['app_id', 'ads.txt_location']
		new_csv_dataframe = pd.DataFrame(data = convert_to_array(), columns = column_names)

		return new_csv_dataframe
		


	if os.path.isfile(file_name) and os.access(file_na,e os.R_OK):
		print("Found existing csv file, modifying...")
		#open file and modify it
		csv_dataframe = modify_existing_csv()
	else: 
		print("No csv file found. Creating new csv file...")
		#no existing file so creating a new one
		csv_dataframe = create_new_csv()
	
	#saving a csv file now
	csv_dataframe.to_csv(file_name)
	print("CSV file complete. File updated with latest information from data.")
	return




