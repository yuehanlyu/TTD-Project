import requests
from threading import Thread
import functools
import re


from config import NUMBER_ATTEMPTS, MAXIMUM_ADS_FILE_SIZE, STREAM_SIZE

"""
File contains code to look at an url and determine 
whether or not there is a valid ads.txt file present

"""


"""
Below function comes from 
https://stackoverflow.com/questions/21827874/timeout-a-python-function-in-windows
"""

def timeout(timeout):
	def deco(func):
		@functools.wraps(func)
		def wrapper(*args, **kwargs):
			res = [Exception('function [%s] timeout [%s seconds] exceeded!' % (func.__name__, timeout))]
			def newFunc():
				try:
					res[0] = func(*args, **kwargs)
				except Exception as e:
					res[0] = e
			t = Thread(target=newFunc)
			t.daemon = True
			try:
				t.start()
				t.join(timeout)
			except Exception as je:
				print('error starting thread')
				raise je
			ret = res[0]
			if isinstance(ret, BaseException):
				raise ret
			return ret
		return wrapper
	return deco

def get_url_text(request):

	def get_text_stream(request):
		"""
		streams the content of webpage to avoid the request hanging (rare edge case)
		"""

		encoding = request.encoding
		content = b''
		size = 0
		for chunk in request.iter_lines(chunk_size = STREAM_SIZE):
			size += len(chunk)
			if size > MAXIMUM_ADS_FILE_SIZE:
				print('Contents too large. Assuming invalid ads.txt file.')
				return ''
			content += chunk
		if encoding:
			return content.decode(encoding)
		else:
			return content.decode()

	def get_text(request):
		return request.text

	content = ''
	#timeout of 2 seconds for function
	func_with_timeout = timeout(timeout = 2)(get_text_stream)
	#protection against extremely large contents that causes the process to hang
	try:
		content = func_with_timeout(request)
	except Exception as e:
		print(e)
	return content

def verify_contents(text):
	check_for_valid_line_regex = r'.+?,.+?, ?(direct|reseller)'
	if re.search(check_for_valid_line_regex, text, flags = re.IGNORECASE):
		return True
	return False


def extensive_check_for_ads_txt(request):

	"""
	After performing the initial status code check, 
	we now need to check for soft 404s and other problematic things
	to verify whether or not there is a ads.txt file present.
	"""

	content = get_url_text(request)
	if not content:
		content = ''
	if (not (
		'<!DOCTYPE' in content or 
		'<!doctype' in content or 
		'<html' in content or 
		'<HTML' in content or 
		'<content:encoded' in content) 
	and #pretty sure this isn't needed anymore due to the regex verification
		('DIRECT' in content or 
		'RESELLER' in content or 
		'direct' in content or 
		'reseller' in content)
	and verify_contents(content[:2000])): #don't want to check the entire file if it's too big
		return True
		
	return False


def check_valid_url_ad_txt(url_path):
	"""
	Given a url, we try to check if it is valid. Returns a boolean 
	"""
	request = None
	#request shouldn't take more than a second or two.
	try:
		request = requests.get(url_path, timeout = 1, stream = True)
	except Exception as e:

		error_info = 'Error encountered pinging ' + url_path + '. Defaulting to no ads.txt here.'
		print(error_info)
		return False
		
	#preliminary check to make sure we get a valid webpage status
	if request.status_code == 200:
		return extensive_check_for_ads_txt(request)
	return False
