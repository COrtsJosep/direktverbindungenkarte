import folium
import shapely
import pandas as pd
import geopandas as gpd

# read the table of existing stations
df_ds = gpd.read_file(  # ds: dienststellen
    filename = 'actual-date-swiss-service-point.csv',
    columns = ['designationOfficial', 'number', 'isoCountryCode', 'hasGeolocation', 'wgs84East', 'wgs84North', 'meansOfTransport'],
)
df_ds.set_index('number', inplace = True)

df_ds = df_ds.loc[
    (df_ds.loc[:, 'hasGeolocation'] == 'true')
    & (df_ds.loc[:, 'isoCountryCode'] == 'CH')
    & (df_ds.loc[:, 'meansOfTransport'].apply(lambda x: 'TRAIN' in x))
]

# create the point geometry for each station
gdf_ds = (
    df_ds
    .set_geometry(
        df_ds.apply(
            lambda row: shapely.Point((row['wgs84East'], row['wgs84North'])),
            axis = 1
        ),
        crs = 'EPSG:4326'
    )
    .loc[:, ['designationOfficial', 'geometry']]
)
del df_ds

# then read the file of train stations served by any route
df_is = gpd.read_file(  # is: ist
    '2026-03-19_istdaten.csv',
    columns = ['LINIEN_ID', 'LINIEN_TEXT', 'BPUIC', 'ANKUNFTSZEIT', 'PRODUKT_ID'],
    ignore_geometry = True,
)
df_is.loc[df_is.loc[:, 'PRODUKT_ID'].isna(), 'PRODUKT_ID'] = 'Zug'

df_is = df_is.loc[
    df_is.loc[:, 'BPUIC'].isin(gdf_ds.index)
    & (df_is.loc[:, 'PRODUKT_ID'] == 'Zug'),
    ['LINIEN_ID', 'LINIEN_TEXT', 'BPUIC', 'ANKUNFTSZEIT']
]

# the arrival time of the first station of the route is empty
df_is['ANKUNFTSZEIT'] = (
    pd
    .to_datetime(df_is.loc[:, 'ANKUNFTSZEIT'], format = '%d.%m.%Y %H:%M')
    .fillna(pd.Timestamp(year = 1, month = 1, day = 1))
)
df_is.sort_values(by = 'ANKUNFTSZEIT', inplace = True)

# now select a station and collect all stations reachable without transfers

ds_id = '8507100'  # Thun Bhf
df_eb = (  # eb: erreichbar
    df_is
    .groupby(by = ['LINIEN_ID', 'LINIEN_TEXT'])
    .apply(lambda chunk: chunk.drop_duplicates(subset = 'BPUIC', keep = 'first'))  # only unique stations
    .groupby(by = ['LINIEN_ID', 'LINIEN_TEXT'])
    .filter(lambda chunk: ds_id in chunk['BPUIC'].values)  # origin station is served by route
)

# now create the routes by joining the coordinates of the stations
line_ids, line_texts, line_descriptions, linestrings = [], [], [], []
for (line_id, line_text), chunk in df_eb.groupby(by = ['LINIEN_ID', 'LINIEN_TEXT']):
    linestring = shapely.LineString(
        [gdf_ds.loc[stop_id, 'geometry'] for stop_id in chunk.loc[:, 'BPUIC']]
    )
    line_description = ' -> '.join([gdf_ds.loc[stop_id, 'designationOfficial'] for stop_id in chunk.loc[:, 'BPUIC']])
    
    line_ids.append(line_id)
    line_texts.append(line_text)
    line_descriptions.append(line_description)
    linestrings.append(linestring)

# join the routes that serve the origin station in a single gdf
gdf_ln = gpd.GeoDataFrame(  # ln: linie
    data = {
        'line_id': line_ids,
        'line_text': line_texts,
        'line_description': line_descriptions,
        'geometry': linestrings,
    },
    crs = gdf_ds.crs,
)

# the only thing left is to map! first we create the map and add the 
# connections
m = gdf_ln.explore(
    tiles = 'CartoDB positron',
    color = 'black',
)

# then add a marker for the origin station
folium.Marker(
    location = tuple(reversed(gdf_ds.loc[ds_id, 'geometry'].coords[0])),
    tooltip = gdf_ds.loc[ds_id, 'designationOfficial'],
    popup = gdf_ds.loc[ds_id, 'designationOfficial'],
    icon = folium.Icon(color = 'red'),
).add_to(m)

# and then add a circle for each reachable station
folium.GeoJson(
    (
        gdf_ds
        .join(
            df_eb.drop_duplicates('BPUIC').set_index('BPUIC'),
            how = 'inner',
        )
        .loc[:, ['designationOfficial', 'geometry']]
    ),
    name = 'Reachable Stations',
    marker = folium.Circle(radius = 1000, fill_color = 'red', color = 'black'),
    tooltip = folium.GeoJsonTooltip(fields = ['designationOfficial']),
).add_to(m)

# export the map
m.save('map.html')
