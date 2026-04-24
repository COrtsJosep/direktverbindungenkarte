#! /usr/bin/bash
echo 'Running 1_download_dienststellen.py'
python 1_download_dienststellen.py
echo 'Running 2_download_istdaten.py'
python 2_download_istdaten.py
echo 'Running 3_clean_dienststellen.py'
python 3_clean_dienststellen.py
echo 'Running 4_download_schienennetz.py'
python 4_download_schienennetz.py
echo 'Running python 5_create_files_per_station.py'
python 5_create_files_per_station.py
