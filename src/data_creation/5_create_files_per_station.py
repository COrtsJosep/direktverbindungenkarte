import folium
import shapely
import pandas as pd
from tqdm import tqdm
import geopandas as gpd
from pathlib import Path
from schienennetz import SchienenNetz
cd = Path(__file__).parent

df_is = pd.read_json(cd.parent / 'assets' / 'istdaten.json', dtype = {'BPUIC': str})
gdf_ds = gpd.read_file(cd.parent / 'assets' / 'dienststellen.geojson').set_index('number')
sn = SchienenNetz()

# now select a station and collect all stations reachable without transfers
df_eb = (  # eb: erreichbar
    df_is
    .groupby(by = 'FAHRT_BEZEICHNER')
    .apply(lambda chunk: chunk.drop_duplicates(subset = 'BPUIC', keep = 'first'))  # only unique stations
    .reset_index()
    .set_index('FAHRT_BEZEICHNER')
)

for ds_id in tqdm(gdf_ds.index):
    line_subset = df_is.loc[df_is.loc[:, 'BPUIC'] == ds_id, 'FAHRT_BEZEICHNER'].drop_duplicates()
    df_eb_sub = df_eb.loc[line_subset].groupby(level = 0)

    # now create the routes by joining the coordinates of the stations
    line_descriptions, stop_sets, multilinestrings = [], [], []
    for ride_id, chunk in df_eb_sub:
        stop_ids = chunk.loc[:, 'BPUIC'].to_list()
        
        stop_set = set(stop_ids)
        if stop_set in stop_sets:
            continue  # already covered this route (or some combination of its stops)
        
        linestring = set()
        for i in range(len(stop_ids) - 1):
            linestring.update(
                sn.get_linestring_route(stop_ids[i], stop_ids[i + 1])
            )
        multilinestring = shapely.MultiLineString(linestring).simplify(tolerance = 1)
        
        line_description = '->'.join([gdf_ds.loc[stop_id, 'designationOfficial'] for stop_id in stop_ids])
        
        stop_sets.append(stop_set)
        line_descriptions.append(line_description)
        multilinestrings.append(multilinestring)

    # join the routes that serve the origin station in a single gdf
    (
        gpd
        .GeoDataFrame(  # ln: linie
            data = {
                'line_description': line_descriptions,
                'geometry': multilinestrings,
            },
            crs = gdf_ds.crs,
        )
        .to_file(cd.parent / 'assets' / f'reachable_net_per_station/{ds_id}.geojson')
    )
    
    (
        gdf_ds
        .join(
            df_eb_sub.obj.drop_duplicates('BPUIC').set_index('BPUIC'),
            how = 'inner',
        )
        .loc[:, ['designationOfficial', 'geometry']]
        .to_file(cd.parent / 'assets' / f'reachable_stations_per_station/{ds_id}.geojson')
    )
