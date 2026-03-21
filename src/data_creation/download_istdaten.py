import pandas as pd
import geopandas as gpd
from pathlib import Path
cd = Path(__file__).parent

# load dienststellen data
gdf_ds = gpd.read_file(cd.parent / 'assets' / 'dienststellen.geojson').set_index('number')

# read the file of train stations served by any route
df_is = gpd.read_file(  # is: ist
    filename = 'https://data.opentransportdata.swiss/dataset/ist-daten-v2/resource_permalink/2026-03-19_istdaten.csv',  # 403 TODO
    columns = ['LINIEN_ID', 'LINIEN_TEXT', 'BPUIC', 'ANKUNFTSZEIT', 'PRODUKT_ID'],
    ignore_geometry = True,
)
df_is.loc[:, 'PRODUKT_ID'] = df_is.loc[:, 'PRODUKT_ID'].fillna('Zug')

df_is = df_is.loc[
    df_is.loc[:, 'BPUIC'].isin(gdf_ds.index)  # only stops from which we have the station
    & (df_is.loc[:, 'PRODUKT_ID'] == 'Zug'),  # only rail travel
    ['LINIEN_ID', 'LINIEN_TEXT', 'BPUIC', 'ANKUNFTSZEIT']
]

# the arrival time of the first station of the route is empty
df_is['ANKUNFTSZEIT'] = (
    pd
    .to_datetime(df_is.loc[:, 'ANKUNFTSZEIT'], format = '%d.%m.%Y %H:%M')
    .fillna(pd.Timestamp(year = 1, month = 1, day = 1))
)
df_is.sort_values(by = 'ANKUNFTSZEIT', inplace = True)

df_is.to_json(cd.parent / 'assets' / 'istdaten.json', date_format = 'iso')
