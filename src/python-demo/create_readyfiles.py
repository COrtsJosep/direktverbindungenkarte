import folium
import shapely
import pandas as pd
from tqdm import tqdm
import geopandas as gpd
from schienennetz import SchienenNetz

df_is = pd.read_json('istdaten.json', dtype = {'BPUIC': str})
gdf_ds = gpd.read_file('dienststellen.geojson').set_index('number')
sn = SchienenNetz()

# now select a station and collect all stations reachable without transfers
df_eb = (  # eb: erreichbar
    df_is
    .groupby(by = ['LINIEN_ID', 'LINIEN_TEXT'])
    .apply(lambda chunk: chunk.drop_duplicates(subset = 'BPUIC', keep = 'first'))  # only unique stations
    .reset_index()
    .set_index(['LINIEN_ID', 'LINIEN_TEXT'])
)

for ds_id in tqdm(gdf_ds.index):
    line_subset = df_is.loc[df_is.loc[:, 'BPUIC'] == ds_id, ['LINIEN_ID', 'LINIEN_TEXT']].drop_duplicates()
    df_eb.loc[list(line_subset.values)]
    df_eb_sub = df_eb.loc[list(line_subset.values)].groupby(level = (0, 1))

    # now create the routes by joining the coordinates of the stations
    line_ids, line_texts, line_descriptions, multilinestrings = [], [], [], []
    for (line_id, line_text), chunk in df_eb_sub:
        stop_ids = chunk.loc[:, 'BPUIC'].to_list()
        linestring = set()
        for i in range(len(stop_ids) - 1):
            linestring.update(
                sn.get_linestring_route(stop_ids[i], stop_ids[i + 1])
            )
        multilinestring = shapely.MultiLineString(linestring).simplify(tolerance = 1)

        line_description = '->'.join([gdf_ds.loc[stop_id, 'designationOfficial'] for stop_id in stop_ids])
        
        line_ids.append(line_id)
        line_texts.append(line_text)
        line_descriptions.append(line_description)
        multilinestrings.append(multilinestring)

    # join the routes that serve the origin station in a single gdf
    gpd.GeoDataFrame(  # ln: linie
        data = {
            'line_id': line_ids,
            'line_text': line_texts,
            'line_description': line_descriptions,
            'geometry': multilinestrings,
        },
        crs = gdf_ds.crs,
    ).to_file(f'reachable_net_readyfiles/{ds_id}.geojson')
    
    (
        gdf_ds
        .join(
            df_eb_sub.obj.drop_duplicates('BPUIC').set_index('BPUIC'),
            how = 'inner',
        )
        .loc[:, ['designationOfficial', 'geometry']]
        .to_file(f'reachable_stations_readyfiles/{ds_id}.geojson')
    )
