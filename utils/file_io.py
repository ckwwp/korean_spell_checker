import warnings
from pathlib import Path
import json

import pandas as pd

from korean_spell_checker.models.interface import Tag
from korean_spell_checker.models.constants import DEFAULT_EXCEL_COL_NAME, DEFAULT_TERMBASE_COL_NAME

warnings.filterwarnings('ignore', message='Data Validation extension is not supported')

def make_dictionary_list(dictionary_file_name: Path) -> list[tuple[str, str]]:
	df = pd.read_csv(dictionary_file_name, dtype=str)
	return [(row.word, Tag[row.category]) for row in df.itertuples(index=False)]

def make_termbase_list(termbase_file_name: Path, col_names: list[str] = None) -> list[str]:
	if col_names is None:
		col_names = [DEFAULT_TERMBASE_COL_NAME]
	df = pd.read_csv(termbase_file_name, usecols=col_names, dtype=str)
	return [i for i in df[DEFAULT_TERMBASE_COL_NAME]]

def get_all_file_paths(folder_name: str, extension: str = None) -> list[Path]:
	if extension is None:
		target_path = Path(folder_name).rglob()
	else:
		target_path = Path(folder_name).rglob(f"*.{extension}")
	return [i.absolute() for i in target_path if not i.name.startswith("~$")]

def read_excel_file(file_path: str, col_names: list[str] = None, drop_na: bool = False) -> pd.DataFrame:
	if col_names is None:
		col_names = [DEFAULT_EXCEL_COL_NAME]
	df = pd.read_excel(file_path, usecols=col_names, dtype=str)
	if drop_na:
		df = df.dropna()
	return df

def read_txt_file(file_path: str, drop_na: bool = False) -> pd.DataFrame:
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.read().splitlines()
    df = pd.DataFrame(lines, columns=['text'])
    if drop_na:
        df = df.dropna()
    return df

def read_json_file(file_path: str, drop_na: bool = False) -> pd.DataFrame:
    with open(file_path, 'r', encoding='utf-8') as f:
        raw_data = json.load(f)
    
    data = raw_data.values()
    df = pd.DataFrame(data, columns=['text'])
    if drop_na:
        df = df.dropna()
    return df