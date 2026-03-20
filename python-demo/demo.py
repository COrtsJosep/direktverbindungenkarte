import folium
import shapely
import pandas as pd
import geopandas as gpd

# read the table of existing stations
gdf_ds = gpd.read_file(  # ds: dienststellen
    filename = 'GEOJSON:dienststellen-gemass-opentransportdataswiss.geojson',
    columns = ['designationofficial', 'number', 'operatingpoint', 'isocountrycode'],
)
gdf_ds.set_index('number', inplace = True)

gdf_ds = gdf_ds.loc[
    (gdf_ds.loc[:, 'operatingpoint'] == 'true')
    & (~gdf_ds.loc[:, 'geometry'].isna())
    & (gdf_ds.loc[:, 'isocountrycode'] == 'CH')
]

# then read the file of train stations served by any route
df_is = gpd.read_file(  # is: ist
    'ist-daten-sbb.geojson',
    columns = ['linien_id', 'linien_text', 'ankunftszeit', 'bpuic', 'fahrt_bezeichner'],
    ignore_geometry = True,
)

# the arrival time of the first station of the route is empty
df_is.loc[:, 'ankunftszeit'] = (
    df_is
    .loc[:, 'ankunftszeit']
    .fillna(pd.Timestamp(year = 1, month = 1, day = 1))
)
df_is.sort_values(by = 'ankunftszeit', inplace = True)

# now select a station and collect all stations reachable without transfers
ds_id = 8507100  # Thun Bhf
df_eb = (  # eb: erreichbar
    df_is
    .groupby(by = ['linien_id', 'linien_text'])
    .apply(lambda chunk: chunk.drop_duplicates(subset = 'bpuic', keep = 'first'))  # only unique stations
    .groupby(by = ['linien_id', 'linien_text'])
    .filter(lambda chunk: (chunk.loc[:, 'bpuic'] == ds_id).any())  # origin station is served by route
)

# now create the routes by joining the coordinates of the stations
line_ids, line_texts, line_descriptions, linestrings = [], [], [], []
for (line_id, line_text), chunk in df_eb.groupby(by = ['linien_id', 'linien_text']):
    linestring = shapely.LineString(
        [gdf_ds.loc[stop_id, 'geometry'] for stop_id in chunk.loc[:, 'bpuic']]
    )
    line_description = ' -> '.join([gdf_ds.loc[stop_id, 'designationofficial'] for stop_id in chunk.loc[:, 'bpuic']])
    
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
    tooltip = gdf_ds.loc[ds_id, 'designationofficial'],
    popup = gdf_ds.loc[ds_id, 'designationofficial'],
    icon = folium.Icon(color = 'red'),
).add_to(m)

# and then add a circle for each reachable station
folium.GeoJson(
    (
        gdf_ds
        .join(
            df_eb.drop_duplicates('bpuic').set_index('bpuic'),
            how = 'inner',
        )
        .loc[:, ['designationofficial', 'geometry']]
    ),
    name = 'Reachable Stations',
    marker = folium.Circle(radius = 1000, fill_color = 'red', color = 'black'),
    tooltip = folium.GeoJsonTooltip(fields = ['designationofficial']),
).add_to(m)

# export the map
m.save('map.html')
