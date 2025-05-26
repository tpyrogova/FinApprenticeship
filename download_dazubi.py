#!/usr/bin/env python
import os, re, math, time, argparse, glob, sys
from typing import Optional, Tuple
from io import BytesIO
import requests
from bs4 import BeautifulSoup
import pandas as pd
import term

# Base URL and directory for saving files
url = "https://www.bibb.de/dienst/dazubi/de/2252.php"
url_excel = "https://www.bibb.de/dienst/dazubi/dazubi/timeserie/download/timeseries.xls?st[attribute]={attribute}&st[countries][0]={country}&st[occupations][0]={occupation}&st[year]={year}&st[search]=&department=10"
output_dir = "data"
output_dir_occ = f"{output_dir}/occ"
output_dir_attr = f"{output_dir}/attr"
output_file = output_dir + '/dazubi_complete.csv'

def parse_arguments():
	parser = argparse.ArgumentParser(
		formatter_class=argparse.ArgumentDefaultsHelpFormatter,
		description="Dowload the files from DAZUBI and convert them to a csv file",
	)
	parser.add_argument('-w', '--start-with', type=int, default=0, help="For Debugging: Start with this file and skip the previous ones.")
	parser.add_argument('-a', '--save-attributes', action='store_true', help="For Debugging: Save csv file after each attribute. You only need this, if you want to check the parsing of single Excel files.")
	parser.add_argument('-d', '--download', action='store_true', help='Start the download process. You have to give this option, to do anything.')
	parser.add_argument('-s', '--sleep', default=1.0, type=float, help='Time to sleep between the individuel downloads. Use a reasonable value to not overwhelming the server.')
	parser.add_argument('-x', '--write-skip', type=int, default=0, help='Write only each x\'th file.')
	parser.add_argument('-n', '--no-sanity-check', action='store_true', help='No sanity check when deleting old files.')
	parser.add_argument('-c', '--compress', action='store_true', help='Compress the CSV files.')
	return parser.parse_args()

def cleanup_dazubi_files(dir, keep: int = 10, sanity_check: bool = True):
	"""
	Deletes all files in the directory matching the pattern 'dazubi_<number>.csv',
	but keeps the 'keep' files with the highest numbers.
	Before deletion, it checks that all files with a lower number are also smaller in size
	and older than those with a higher number. Only if this is true for all files, deletion is performed.

	Args:
		dir (str): Path to the directory containing the files to be cleaned up.
		keep (int): Number of most recent files to keep. Older files will be deleted if conditions are met.
	Raises:
		RuntimeError: If a file with a lower number is not smaller and older than a file with a higher number.
	"""
	pattern = os.path.join(dir, "dazubi_*.csv*")
	files = []
	for path in glob.glob(pattern):
		basename = os.path.basename(path)
		match = re.match(r'dazubi_(\d+)\.csv.*$', basename)
		if match:
			num = int(match.group(1))
			stat = os.stat(path)
			files.append({
				"path": path,
				"num": num,
				"size": stat.st_size,
				"mtime": stat.st_mtime
			})
	if len(files) <= keep:
		term.up(value=1)
		term.clearLine()
		print("Nothing to do, there are", len(files), "files (less than or equal to", keep, ").")
		return

	# Sort by number (ascending)
	files.sort(key=lambda x: x["num"])

	if sanity_check:
		# Check: Each file with a lower number must be smaller and older than each file with a higher number
		for i in range(len(files)):
			for j in range(i+1, len(files)):
				if not (files[i]["size"] <= files[j]["size"] and files[i]["mtime"] <= files[j]["mtime"]):
					raise RuntimeError(
						f"File {files[i]['path']} is not smaller/older than {files[j]['path']}.\n"
						f"Properties of files:\n\t{files[i]}\nvs.\n\t{files[j]}"
					)

	for f in files[:-keep]:
		term.up(value=1)
		term.clearLine()
		print("Deleting:", f['path'])
		os.remove(f['path'])

from typing import Literal

def save_dataframe(
	df: pd.DataFrame,
	filename: str = output_file,
	compress: bool = False,
	# compression: Literal['bz2', 'zip', 'gzip', 'xz'] = None,
	delete_old_files: bool = True,
	sanity_check: bool = True
):
	"""
	Safely save a pandas DataFrame to a CSV file.

	The DataFrame is first written to a temporary file. Once writing is successful, the temporary file is atomically
	moved to the target location to prevent data corruption. If the target directory does not exist, it is created.
	If a KeyboardInterrupt, OSError, or RuntimeError occurs during saving, the temporary file is removed before re-raising the exception.
	If delete_old_files is True, old files in the directory are cleaned up after saving.

	Args:
		df (pd.DataFrame): The DataFrame to save.
		filename (str, optional): The path to the output CSV file. Defaults to the global 'output_file'.
		compression (Literal['bz2', 'zip', 'gzip', 'xz'], optional): Compression mode. Allowed values are the same as pandas.DataFrame.to_csv 'compression' parameter.
		delete_old_files (bool, optional): If True, calls cleanup_dazubi_files to remove old files after saving.

	Raises:
		KeyboardInterrupt: If interrupted, removes the temporary file if it exists and re-raises the exception.
		OSError: If an OS error occurs, removes the temporary file if it exists and re-raises the exception.
		RuntimeError: If cleanup_dazubi_files raises an error, removes the temporary file if it exists and re-raises the exception.
	"""
	compression = 'bz2'
	dirname = os.path.dirname(filename)
	if dirname and not os.path.exists(dirname):
		os.makedirs(dirname, exist_ok=True)
	if compress:
		filename += '.' + compression
	tmp_filename = filename + '.tmp'
	try:
		term.up(value=2)
		term.clearLine()
		print(f'Saving: {filename}')
		term.down(value=1)
		df.to_csv(tmp_filename, compression=compression if compress else None)
		os.replace(tmp_filename, filename)
		if delete_old_files:
			cleanup_dazubi_files(dirname, sanity_check=sanity_check)
	except (KeyboardInterrupt, OSError, RuntimeError):
		if os.path.exists(tmp_filename):
			os.remove(tmp_filename)
		raise

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
	pattern = re.compile(r'dazubi_(\d+)\.csv.*$')
	max_number = -1
	max_filename = None
	if os.path.exists(output_dir_occ):
		for filename in os.listdir(output_dir_occ):
			match = pattern.match(filename)
			if match:
				number = int(match.group(1))
				if number > max_number:
					max_number = number
					max_filename = filename
	if max_filename is not None:
		try:
			df = pd.read_csv(os.path.join(output_dir_occ, max_filename), index_col=0)
			print(f'===> restore file {max_filename} with {len(df)} rows')
			return max_number+1, df
		except Exception as e:
			print(f'{term.red}Can not read the file {max_filename}. Remove the file and restart.', file=sys.stderr)
			raise
	else:
		print('===> Nothing to restore')
		return 0, pd.DataFrame()

def download_convert(url: str, retries=5) -> dict[str, pd.DataFrame]:
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
			xls = pd.read_excel(BytesIO(response.content), sheet_name=None)
			return xls
		except Exception as e:
			print(f'{r} attempt, Exception: {type(e).__name__} - {e}')
			if response is not None:
				print(f'Status: {response.status_code}, Content-Type: {response.headers.get("Content-Type")}, Content-Length: {response.headers.get("Content-Length")}')
			if r >= retries: raise
			else: r += 1

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
	cnt_write = 0
	start_with, df = restore_download()
	start_with = max(start_with, args.start_with)
	print('\n\n\n')
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
						term.up(value=2)
						term.up(value=1)
						term.clearLine()
						term.up(value=1)
						term.clearLine()
						print(f'{cnt:6d} / {complete} {round(time.time() - start):6d}s {url_download}')
						term.down(value=2)
						xls = download_convert(url_download)
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
								if args.save_attributes: save_dataframe(df_occ, f'{output_dir_attr}/dazubi_{cnt:06d}.csv', compress=args.compress, sanity_check=not args.no_sanity_check)
						# add sleep to avoid overwhelming the server
						time.sleep(args.sleep)
					cnt += 1
				if (len(df_occ) > 0):
					df = pd.concat([df, df_occ])
					df.reset_index(inplace=True, drop=True)
					if cnt_write >= args.write_skip:
						save_dataframe(df, f'{output_dir_occ}/dazubi_{cnt:06d}.csv', sanity_check=not args.no_sanity_check, compress=args.compress)
						cnt_write = 0
					else:
						cnt_write += 1
		save_dataframe(df, compress=args.compress)
	print(f'===> {cnt} files donwloaded')
	df.info()

if __name__ == '__main__':
	args = parse_arguments()
	main(args)