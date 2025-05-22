import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import os
import math
from io import BytesIO
import argparse
from termcolor import colored

# Base URL and directory for saving files
url = "https://www.bibb.de/dienst/dazubi/de/2252.php"
url_excel = "https://www.bibb.de/dienst/dazubi/dazubi/timeserie/download/timeseries.xls?st[attribute]={attribute}&st[countries][0]={country}&st[occupations][0]={occupation}&st[year]={year}&st[search]=&department=10"
output_dir = "data"
output_file = output_dir + '/dazubi.csv'

def parse_arguments():
	parser = argparse.ArgumentParser()
	parser.add_argument('-c', '--cnt', type=int, default=0, help="For Debugging: Start with this file")
	return parser.parse_args()

def save_dataframe(df, filename=output_file):
	dirname = os.path.dirname(filename)
	if dirname and not os.path.exists(dirname):
		os.makedirs(dirname, exist_ok=True)
	df.to_csv(filename)

def get_dropdown_values(soup, select_id):
	"""Extract values from dropdown menu"""
	select = soup.find('select', {'id': select_id})
	if not select:
		return []
	options = select.find_all('option')
	return [(option['value'], option.text.strip()) for option in options if option['value']]

def check_valid(value):
	return type(value) == str or not math.isnan(value)

def rename_columns(df):
	try:
		# for some files the header is more than one line
		# we take the column with the year, there we can just check the type, if it's int, we have reached the data part
		start_of_data = 0
		for row in df.iloc[:, 0]:
			if type(row) == int: break
			start_of_data += 1
		df_header = df.iloc[0:start_of_data]
		df = df.iloc[start_of_data:].copy()
		df.reset_index(inplace=True, drop=True)
		new_column_name_start = None
		new_column_names = {}
		for col in df_header:
			for ind in range(0, start_of_data):
				header = df_header[col][ind]
				if check_valid(header):
					if ind == 0:
						new_column_name_start = header
						new_column_name = new_column_name_start
					else:
						new_column_name += f' {header}'
			new_column_names[col] = new_column_name.replace('\n', ' ')
		df.rename(columns=new_column_names, inplace=True)
	except Exception as e:
		print(type(e).__name__, '-', e)
		print(f'start_of_data: {start_of_data}')
		print(df_header.head())
		print(df_header.info())
		print(new_column_names)
		raise
	return df

def main(args):
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
	df = pd.DataFrame()
	start = time.time()
	for country_id, country_name in countries:
		for occ_id, occ_name in occupations:
			df_occ = pd.DataFrame()
			for attr_id, attr_name in attributes:
				year_id, year_name = years[0]
				url_download = url_excel.format(attribute=attr_id, occupation=occ_id, year=year_id, country=country_id)
				print(f'{cnt:5d} / {complete} {round(time.time() - start):6d}s', colored(url_download, 'green' if cnt >= args.cnt else 'red'))
				if cnt >= args.cnt:
					resp_xls = requests.get(url_download)
					xls = pd.read_excel(BytesIO(resp_xls.content), sheet_name=None)
					for sheet, df_attr in xls.items():
						if sheet != 'Deckblatt':
							df_attr = rename_columns(df_attr)
							df_attr.insert(1, 'Beruf', occ_name)
							df_attr.insert(2, 'Region', country_name)
							if 'Jahr' in df_occ.columns and 'Jahr' in df_attr.columns: 
								df_occ = pd.merge(df_occ, df_attr, suffixes=(None, '_'+attr_id), on=['Jahr', 'Beruf', 'Region'], how='outer')
							else:
								df_occ = pd.concat([df_occ, df_attr], axis=1)
							save_dataframe(df_occ, f'{output_dir}/attr/dazubi_{cnt:06d}.csv')
					# add sleep to avoid overwhelming the server
					time.sleep(1)
				cnt += 1
			df = pd.concat([df, df_occ])
			df.reset_index(inplace=True, drop=True)
			save_dataframe(df, f'{output_dir}/occ/dazubi_{cnt:06d}.csv')
	print(f'===> {cnt} files donwloaded')
	df.info()
	save_dataframe(df)

if __name__ == '__main__':
	main(parse_arguments())