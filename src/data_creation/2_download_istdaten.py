import requests
import pandas as pd
import geopandas as gpd
from pathlib import Path
from datetime import datetime, timedelta
cd = Path(__file__).parent

# load dienststellen data
gdf_ds = gpd.read_file(cd.parent / 'assets' / 'dienststellen_dirty.geojson').set_index('number')

# create txt with last update time
yesterday = datetime.strftime(datetime.now() - timedelta(days = 1), '%Y-%m-%d')
with open(cd.parent.parent / 'last_update.txt', mode = 'w') as f:  # for version control
    f.write(f'Last update: {datetime.now()}\nIst-data from day: {yesterday}')

# download and read the file of train stations served by any route
url_is = f'https://data.opentransportdata.swiss/dataset/ist-daten-v2/resource_permalink/{yesterday}_istdaten.csv'
path_is = cd / f'{yesterday}_istdaten.csv'
with open(path_is, mode = 'wb') as f:
    f.write(requests.get(url_is).content)

# read ist-data
df_is = gpd.read_file(  # is: ist
    filename = path_is,
    columns = [
        'HALTESTELLEN_NAME', 'FAHRT_BEZEICHNER', 'BPUIC',
        'ANKUNFTSZEIT', 'PRODUKT_ID', 'LINIEN_TEXT', 'ZUSATZFAHRT_TF',
    ],
    ignore_geometry = True,
)
path_is.unlink()  # delete the raw file once loaded
df_is.loc[:, 'PRODUKT_ID'] = df_is.loc[:, 'PRODUKT_ID'].fillna('Zug')

# the following stations should be merged with Brig, Lugano and Locarno, respectively
df_is.loc[df_is.loc[:, 'HALTESTELLEN_NAME'] == 'Brig Bahnhofplatz', 'BPUIC'] = '8501609'
df_is.loc[df_is.loc[:, 'HALTESTELLEN_NAME'] == 'Lugano FLP', 'BPUIC'] = '8505300'
df_is.loc[df_is.loc[:, 'HALTESTELLEN_NAME'] == 'Locarno FART', 'BPUIC'] = '8505400'

df_is = df_is.loc[
    df_is.loc[:, 'BPUIC'].isin(gdf_ds.index)       # only stops from which we have the station
    & (df_is.loc[:, 'PRODUKT_ID'] == 'Zug')        # only rail travel
    & (df_is.loc[:, 'LINIEN_TEXT'] != 'ATZ')       # no car train shuttle
    & (df_is.loc[:, 'ZUSATZFAHRT_TF'] == 'false'), # no extraordinary rides
    ['FAHRT_BEZEICHNER', 'BPUIC', 'ANKUNFTSZEIT']  # drop unnecessary columns
]

# the arrival time of the first station of the route is empty
df_is['ANKUNFTSZEIT'] = (
    pd
    .to_datetime(df_is.loc[:, 'ANKUNFTSZEIT'], format = '%d.%m.%Y %H:%M')
    .fillna(pd.Timestamp(year = 1, month = 1, day = 1))
)
df_is.sort_values(by = 'ANKUNFTSZEIT', inplace = True)

df_is.to_json(cd.parent / 'assets' / 'istdaten.json', date_format = 'iso')
