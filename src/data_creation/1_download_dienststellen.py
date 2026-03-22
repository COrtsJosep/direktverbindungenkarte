import shapely
import requests
import geopandas as gpd
from pathlib import Path
cd = Path(__file__).parent

# download and read the table of existing stations
url_ds = 'https://data.opentransportdata.swiss/dataset/service-point-v2/resource_permalink/actual-date-swiss-service-point.csv'
path_ds = cd / 'actual-date-swiss-service-point.csv'
with open(path_ds, mode = 'wb') as f:
    f.write(requests.get(url_ds).content)
    
df_ds = gpd.read_file(  # ds: dienststellen
    filename = path_ds,
    columns = ['designationOfficial', 'number', 'isoCountryCode', 'hasGeolocation', 'wgs84East', 'wgs84North', 'meansOfTransport'],
)
path_ds.unlink()  # delete the raw file once loaded
df_ds.set_index('number', inplace = True)

df_ds = df_ds.loc[
    (df_ds.loc[:, 'hasGeolocation'] == 'true')
    & (df_ds.loc[:, 'isoCountryCode'] == 'CH')
    & (df_ds.loc[:, 'meansOfTransport'].apply(lambda x: 'TRAIN' in x))  # station serves trains
]

# manual corrections
df_ds.loc[df_ds.loc[:, 'designationOfficial'] == 'Zürich HB', ['wgs84East', 'wgs84North']] = ['8.539239', '47.378194']

# create the point geometry for each station
(
    df_ds
    .set_geometry(
        df_ds.apply(
            lambda row: shapely.Point((row['wgs84East'], row['wgs84North'])),
            axis = 1
        ),
        crs = 'EPSG:4326'
    )
    .loc[:, ['designationOfficial', 'geometry']]
    .to_file(cd.parent / 'assets' / 'dienststellen_dirty.geojson')
)
