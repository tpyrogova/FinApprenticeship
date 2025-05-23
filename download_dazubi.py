#!/usr/bin/env python
import os, re, math, time, argparse
from typing import Optional, Tuple
from io import BytesIO
import requests
from bs4 import BeautifulSoup
import pandas as pd
from termcolor import colored

# Base URL and directory for saving files
url = "https://www.bibb.de/dienst/dazubi/de/2252.php"
url_excel = "https://www.bibb.de/dienst/dazubi/dazubi/timeserie/download/timeseries.xls?st[attribute]={attribute}&st[countries][0]={country}&st[occupations][0]={occupation}&st[year]={year}&st[search]=&department=10"
output_dir = "data"
output_dir_occ = f"{output_dir}/occ"
output_dir_attr = f"{output_dir}/attr"
output_file = output_dir + '/dazubi.csv'

def parse_arguments():
	parser = argparse.ArgumentParser(
		formatter_class=argparse.ArgumentDefaultsHelpFormatter,
		description="Dowload the files from DAZUBI and convert them to a csv file",
	)
	parser.add_argument('-w', '--start-with', type=int, default=0, help="For Debugging: Start with this file and skip the previous ones.")
	parser.add_argument('-a', '--save-attributes', action='store_true', help="For Debugging: Save csv file after each attribute. You only need this, if you want to check the parsing of single Excel files.")
	parser.add_argument('-d', '--download', action='store_true', help='Start the download process. You have to give this option, to do anything.')
	parser.add_argument('-s', '--sleep', default=1, type=int, help='Time to sleep between the individuel downloads. Use a reasonable value to not overwhelming the server.')
	return parser.parse_args()

def save_dataframe(df: pd.DataFrame, filename: str = output_file):
	dirname = os.path.dirname(filename)
	if dirname and not os.path.exists(dirname):
		os.makedirs(dirname, exist_ok=True)
	df.to_csv(filename)

def get_dropdown_values(soup: BeautifulSoup, select_id: str):
	"""Extract values from dropdown menu"""
	select = soup.find('select', {'id': select_id})
	if not select:
		return []
	options = select.find_all('option')
	return [(option['value'], option.text.strip()) for option in options if option['value']]

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

from pandas import DataFrame

def restore_download() -> Tuple[int, DataFrame]:
	'''
	if we already donwloaded files, create a DataFrame from the file with the highest number (the last file)

	The restore only works, if the countries and occupation stays the same between the download sessions
	The attributes doesn't matter, because the downloads for the attributes are not restored
	
	return
		highest number + 1 - use this as index for the next file to download
		DataFrame with data from the last csv file
	'''
	pattern = re.compile(r'dazubi_(\d+)\.csv$')
	max_number = -1
	max_filename = None
	for filename in os.listdir(output_dir_occ):
		match = pattern.match(filename)
		if match:
			number = int(match.group(1))
			if number > max_number:
				max_number = number
				max_filename = filename
	if max_filename is not None:
		print(f'===> restore file {max_filename}')
		return max_number+1, pd.read_csv(os.path.join(output_dir_occ, max_filename))
	else:
		print('===> Nothing to restore')
		return 0, pd.DataFrame()

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
	complete = len(attributes) * len(occupations) * len(countries)
	
	cnt = 0
	start_with, df = restore_download()
	start_with = max(start_with, args.start_with)
	if (args.download):
		start = time.time()
		# iterate over each country, each occupation and each attribute
		# for the year we just take the first value, than we get all years
		for country_id, country_name in countries:
			for occ_id, occ_name in occupations:
				df_occ = pd.DataFrame()
				# we create a DataFrame that contains each attribute for the current country and job
				# this DataFrame is appended to the final DataFrame
				for attr_id, attr_name in attributes:
					# for the attributes DataFrame, we create a separate DataFrame for each sheet in each Excel file
					# these DataFrames are merged on the 'Jahr' column
					year_id, year_name = years[0]
					url_download = url_excel.format(attribute=attr_id, occupation=occ_id, year=year_id, country=country_id)
					if cnt >= start_with:
						print(f'{cnt:5d} / {complete} {round(time.time() - start):6d}s {url_download}')
						resp_xls = requests.get(url_download)
						xls = pd.read_excel(BytesIO(resp_xls.content), sheet_name=None)
						for sheet, df_attr in xls.items():
							if sheet != 'Deckblatt':
								df_attr = rename_columns(df_attr)
								df_attr.insert(1, 'Beruf', occ_name)
								df_attr.insert(2, 'Region', country_name)
								if 'Jahr' in df_occ.columns and 'Jahr' in df_attr.columns: 
									# take Beruf and Region in the on-clause to not duplicate these columns
									df_occ = pd.merge(df_occ, df_attr, suffixes=(None, f'_{attr_id}'), on=['Jahr', 'Beruf', 'Region'], how='outer')
								else:
									df_occ = pd.concat([df_occ, df_attr], axis=1)
								if args.save_attributes: save_dataframe(df_occ, f'{output_dir_attr}/dazubi_{cnt:06d}.csv')
						# add sleep to avoid overwhelming the server
						time.sleep(args.sleep)
					cnt += 1
				df = pd.concat([df, df_occ])
				df.reset_index(inplace=True, drop=True)
				save_dataframe(df, f'{output_dir_occ}/dazubi_{cnt:06d}.csv')
		save_dataframe(df)
	print(f'===> {cnt} files donwloaded')
	df.info()

if __name__ == '__main__':
	args = parse_arguments()
	main(args)