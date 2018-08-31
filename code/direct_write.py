'''
Experimental method of processing and writing directl into DynamoDB.
Implementing so we can test the time it takes compared to first writing it
into a csv file.

Update: 08/21/18
This has equal performance to  writing to a csv file, so we 
can go with this since it removes the intermediate file 

'''
import sys
import time
import boto3

from config import MAX_BATCH_SIZE, store_keywords_dict
from check_url import *
from extractor import *
from write_to_dynamo import write_items_batch, find_table, add_item_to_table
from utils import parse_for_specific_parameter
#from main import determine_app_store



'''
Functions include manually defined variables for now while we get set up and running.
Will update to make it flexible later
'''

def determine_app_store(file_name):
	google_play_string = 'https://play.google.com/store'


	#dummy strings for now until we get Apple/Tencent data
	apple_ios_string = 'http://itunes.apple.com'
	tencent_string = 'https://tencent.com/store'


	#we just need to check the first line assuming one data file only contains info from one app store
	with open(file_name, 'r', encoding = 'utf-8') as f:
		first_line = f.readline()
		if google_play_string in first_line:
			return 'Google'
		if apple_ios_string in first_line:
			return 'Apple'
		if tencent_string in first_line:
			return 'Tencent'

	print("Please examine your data file. No valid app store detected.")
	print("Exiting...")
	exit()
	return ''




def format_batch(batch):
	'''
	processes each entry in batch into a format that can be pushed to Dynamo
	'''
	formatted = []
	for item in batch:
		app_id, location = item
		formatted_item = {
			'App_ID': str(app_id),
			'FileLocation': str(location) 
		}
		formatted.append(formatted_item)
	return formatted


def process_file_into_dynamo(file_name):
	print("Processing file into Dynamo...")
	app_store = determine_app_store(file_name)
	app_id_marker, market_url_marker, seller_url, package = store_keywords_dict[app_store]	
	extractor = Extractor(seller_url, package)

	table = find_table(app_store)

	with open(file_name, 'r', encoding = 'utf-8') as f:
		current_entry = f.readline()
		current_batch = []
		while current_entry:
			app_id = parse_for_specific_parameter(app_id_marker, current_entry)
			market_url = parse_for_specific_parameter(market_url_marker, current_entry)
			if app_id and market_url:
				corresponding_url = extractor.look_for_ads_txt_url(current_entry)
			if corresponding_url == '':
				corresponding_url = 'No ads.txt file found.'

			current_batch.append(((app_id, market_url), corresponding_url))

			if len(current_batch) % MAX_BATCH_SIZE == 0:
				formatted_batch = format_batch(current_batch)
				write_items_batch(formatted_batch, table)
				current_batch = [] #empty out the current batch

			current_entry = f.readline()
		f.close()
	print("Finished processing file into Dynamo.")


def s3_determine_app_store(example_data_entry):
	google_play_string = 'https://play.google.com/store'
	apple_ios_string = 'itunes.apple.com'
	tencent_string = 'tencent'
	if google_play_string in example_data_entry:
		return 'Google'
	if apple_ios_string in example_data_entry:
		return 'Apple'
	if tencent_string in example_data_entry:
		return 'Tencent'
	print("Please examine your data file. No valid app store detected.")
	print("Exiting...")
	exit()
	return 

def process_s3_object_into_dynamo(s3_object_key, s3_bucket, data):
	print("Processing s3 object into Dynamo...")
	app_store = s3_determine_app_store(data[0])
	app_id_marker, market_url_marker, seller_url, package = store_keywords_dict[app_store]	
	extractor = Extractor(seller_url, package)
	table = find_table(app_store)

	current_batch = []
	for entry_index in range(len(data)):
		current_entry = data[entry_index]
		app_id = parse_for_specific_parameter(app_id_marker, current_entry)
		market_url = parse_for_specific_parameter(market_url_marker, current_entry)
		if app_id and market_url:
			corresponding_url = extractor.look_for_ads_txt_url(current_entry)
		if corresponding_url == '':
			corresponding_url = 'No ads.txt file found.'

		#add_item_to_table(table, str((app_id, market_url)), corresponding_url)
		current_batch.append(((app_id, market_url), corresponding_url))

		if len(current_batch) % MAX_BATCH_SIZE == 0:
			formatted_batch = format_batch(current_batch)
			write_items_batch(formatted_batch, table)
			current_batch = []

	print("Finished processing s3 object into Dynamo.")
	return







def main(args):
	start_time = time.time()
	process_file_into_dynamo(args[1])
	print("Processing file took ", time.time() - start_time, " seconds.")


if __name__ == "__main__":
	main(sys.argv)





