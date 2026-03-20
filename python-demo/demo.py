import geopandas as gpd

df_ds = gpd.read_file(
    filename = 'dienststellen-gemass-opentransportdataswiss.csv',
    columns = ['designationOfficial', 'Geopos', 'number', 'operatingPoint'],
)

df_ds = df_ds.loc[
    (df_ds.loc[:, 'operatingPoint'] == 'true')
    & (df_ds.Geopos != '')
]

gdf_ds = df_ds.set_geometry(
    col = df_ds.loc[:, 'Geopos'].apply(lambda s: shapely.Point(reversed(s.split(', ')))),
    crs = 'EPSG:4326',
)

m = gdf_ds.sample(1000).explore(
    tiles = 'CartoDB dark_matter',
    tooltip = 'designationOfficial',
    color = 'white',
    marker_kwds = {'radius': 1},
)

m.save('map.html')
