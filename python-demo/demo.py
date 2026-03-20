import folium
import shapely
import pandas as pd
import geopandas as gpd
from schienennetz import SchienenNetz

df_is = pd.read_json('istdaten.json', dtype = {'BPUIC': str})
gdf_ds = gpd.read_file('dienststellen.geojson').set_index('number')
sn = SchienenNetz()

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
line_ids, line_texts, line_descriptions, multilinestrings = [], [], [], []
for (line_id, line_text), chunk in df_eb.groupby(by = ['LINIEN_ID', 'LINIEN_TEXT']):
    stop_ids = chunk.loc[:, 'BPUIC'].to_list()
    linestring = set()
    for i in range(len(stop_ids) - 1):
        linestring.update(
            sn.get_linestring_route(stop_ids[i], stop_ids[i + 1])
        )
    multilinestring = shapely.MultiLineString(linestring)

    line_description = '->'.join([gdf_ds.loc[stop_id, 'designationOfficial'] for stop_id in stop_ids])
    
    line_ids.append(line_id)
    line_texts.append(line_text)
    line_descriptions.append(line_description)
    multilinestrings.append(multilinestring)

# join the routes that serve the origin station in a single gdf
gdf_ln = gpd.GeoDataFrame(  # ln: linie
    data = {
        'line_id': line_ids,
        'line_text': line_texts,
        'line_description': line_descriptions,
        'geometry': multilinestrings,
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
