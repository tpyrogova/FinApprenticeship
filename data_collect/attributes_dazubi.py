#!/usr/bin/env python
import os, re, math, time, argparse, glob, sys
from typing import Optional, Tuple
from io import BytesIO
import requests
from bs4 import BeautifulSoup
import pandas as pd
import term

url = "https://www.bibb.de/dienst/dazubi/de/2252.php"
url_excel = "https://www.bibb.de/dienst/dazubi/dazubi/timeserie/download/timeseries.xls?st[attribute]={attribute}&st[countries][0]={country}&st[occupations][0]={occupation}&st[year]={year}&st[search]=&department=10"
output_dir = "data"

def get_dropdown_values(soup: BeautifulSoup, select_id: str):
	"""Extract values from dropdown menu"""
	select = soup.find('select', {'id': select_id})
	if not select:
		return []
	options = select.find_all('option')
	return [(option['value'], option.text.strip()) for option in options if option['value']]

def download(url: str, retries=5):
	xls = None
	r = 0
	# we use while instead of for, so pylace doesn't complain about the return type
	# if the creation of the DataFrame was successful, we return it
	# if we got an exception, we retry a fixed number of times and than raise the error 
	# in both cases we break out of the while loop
	while True:
		response = None
		try:
			response = requests.get(url)
			return response
			oo
		except Exception as e:
			print(f'{r} attempt, Exception: {type(e).__name__} - {e}')
			if response is not None:
				print(f'Status: {response.status_code}, Content-Type: {response.headers.get("Content-Type")}, Content-Length: {response.headers.get("Content-Length")}')
			if r >= retries: raise
			else: r += 1

def check_valid(value: object) -> bool:
	'''
	check if value is not a NaN
	'''
	return isinstance(value, str) or (isinstance(value, float) and not math.isnan(value))

def rename_columns(df: pd.DataFrame) -> pd.DataFrame:
	df_header = None
	columns = {}
	start_of_data = 0
	try:
		# for some files the header is more than one line
		# we take the column with the year, there we can just check the type, if it's int, we have reached the data part
		for row in df.iloc[:, 0]:
			if type(row) == int: break
			start_of_data += 1
		df_header = df.iloc[0:start_of_data]
		df = df.iloc[start_of_data:].copy()
		df.reset_index(inplace=True, drop=True)
		new_column_name_start = None
		current_column_name = ''
		for col in df_header:
			for ind in range(0, start_of_data):
				header = df_header[col][ind]
				if check_valid(header):
					if ind == 0:
						new_column_name_start = header
						current_column_name = new_column_name_start
					else:
						current_column_name += f' {header}'
			columns[col] = current_column_name.replace('\n', ' ')
		df.rename(columns=columns, inplace=True)
	except Exception as e:
		# the parsing of the header failed, so show some information for digging into the problem
		print(type(e).__name__, '-', e)
		print(f'start_of_data: {start_of_data}')
		if df_header is not None:
			print(df_header.head())
			print(df_header.info())
		else:
			print('df_header is not defined')
		print('columns: ', columns)
		raise
	return df

def rename_columns_2(df: pd.DataFrame) -> pd.DataFrame:
	df_header = None
	columns = {}
	start_of_data = 0
	try:
		# for some files the header is more than one line
		# we take the column with the year, there we can just check the type, if it's int, we have reached the data part
		for row in df.iloc[:, 0]:
			if type(row) == int: break
			start_of_data += 1
		df_header = df.iloc[0:start_of_data]
		df = df.iloc[start_of_data:].copy()
		df.reset_index(inplace=True, drop=True)
		new_column_name_start = None
		current_column_name = ''
		for col in df_header:
			for ind in range(0, start_of_data):
				header = df_header[col][ind]
				if check_valid(header):
					if ind == 0:
						new_column_name_start = header
						current_column_name = new_column_name_start
					else:
						current_column_name = f'{new_column_name_start} {header}'
			columns[col] = current_column_name.replace('\n', ' ')
		df.rename(columns=columns, inplace=True)
	except Exception as e:
		# the parsing of the header failed, so show some information for digging into the problem
		print(type(e).__name__, '-', e)
		print(f'start_of_data: {start_of_data}')
		if df_header is not None:
			print(df_header.head())
			print(df_header.info())
		else:
			print('df_header is not defined')
		print('columns: ', columns)
		raise
	return df

def save_dataframe(
	df: pd.DataFrame,
	filename: str,
):
	dirname = os.path.dirname(filename)
	if dirname and not os.path.exists(dirname):
		os.makedirs(dirname, exist_ok=True)
	tmp_filename = filename + '.tmp'
	try:
		print(f'Saving: {filename}')
		df.to_csv(tmp_filename, sep=';')
		os.replace(tmp_filename, filename)
	except (KeyboardInterrupt, OSError, RuntimeError):
		if os.path.exists(tmp_filename):
			os.remove(tmp_filename)
		raise

def parse_arguments():
	parser = argparse.ArgumentParser(
		formatter_class=argparse.ArgumentDefaultsHelpFormatter,
		description="Dowload the files from DAZUBI and convert them to a csv file",
	)
	parser.add_argument('-d', '--download', action='store_true', help='Start the download process. You have to give this option, to do anything.')
	parser.add_argument('-s', '--sleep', default=1.0, type=float, help='Time to sleep between the individuel downloads. Use a reasonable value to not overwhelming the server.')
	return parser.parse_args()

def main(args: argparse.Namespace):
	# Get initial page
	response = requests.get(url)
	soup = BeautifulSoup(response.content, 'html.parser')

	# Get all dropdown values
	attributes = get_dropdown_values(soup, 'st_attribute')
	occupations = get_dropdown_values(soup, 'st_occupations')
	countries = get_dropdown_values(soup, 'st_countries')
	years = get_dropdown_values(soup, 'st_year')
	
	print(f'===> {len(attributes)} attributes, {len(occupations)} occupations, {len(countries)} countries, {len(years)} years')

	df_sheets = pd.DataFrame()
	
	if (args.download):
		lst_old_names = []
		lst_new_names = []
		for attr_id, attr_name in attributes:
			country_id, country_name = countries[0]
			occ_id, occ_name = occupations[0]
			year_id, year_name = years[0]
			url_download = url_excel.format(attribute=attr_id, occupation=occ_id, year=year_id, country=country_id)
			response = download(url_download)
			filepath = output_dir + '/attr/' + attr_name.replace('/', '_')
			xls = pd.read_excel(BytesIO(response.content), sheet_name=None)
			# with open(filepath + '.xlsx', 'wb') as file:
			# 	for chunk in response.iter_content(chunk_size=8192):
			# 		file.write(chunk)
			lst_features = list(xls.keys())
			for sheet_name, df_xls in xls.items():
				if sheet_name != 'Deckblatt':
					# df_xls_old = rename_columns(df_xls.copy())
					# df_xls_new = rename_columns_2(df_xls.copy())
					# lst_old_names.extend(df_xls_old.columns)
					# lst_new_names.extend(df_xls_new.columns)
					df_xls = rename_columns_2(df_xls)
					lst_features.extend(df_xls.columns)
					# save_dataframe(df_xls, filepath + '.csv')
			# print(f'attribute: {attr_name}, number of features: {len(lst_features)}')
			df_sheets = pd.concat([df_sheets, pd.DataFrame(lst_features, columns=[attr_name])], axis=1)

		pd.DataFrame(df_sheets.columns).to_excel('data/new_names.xlsx')
		# column_renamer = dict(zip(lst_old_names, lst_new_names))
		# df_complete = pd.read_parquet('data/dazubi_complete.parquet')
		# df_complete.rename(columns=column_renamer, inplace=True)
		# # df_complete.to_parquet('data/dazubi_complete_2.parquet')
		# df_complete.to_pickle('data/dazubi_complete_2.pickle')
		# print(column_renamer)
		# print(df_sheets.info())
		# df_sheets.to_excel(output_dir + '/dazubi_attributes_2.xlsx')

if __name__ == '__main__':
	args = parse_arguments()
	main(args)
