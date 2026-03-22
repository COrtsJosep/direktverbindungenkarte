#! /usr/bin/bash
python 1_download_dienststellen.py
python 2_download_istdaten.py
python 3_clean_dienststellen.py
python 4_download_schienennetz.py
python 5_create_files_per_station.py
