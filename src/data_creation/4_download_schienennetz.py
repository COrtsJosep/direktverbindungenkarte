import shapely
import geopandas as gpd
from pathlib import Path
cd = Path(__file__).parent

gdf_ka = (  # schienennetz kanten
    gpd
    .read_file(
        filename = 'https://data.geo.admin.ch/ch.swisstopo.swisstne-base/swisstne-base_2025-03-05/swisstne-base_2025-03-05_swisstnebase_2056_5728.gpkg.zip',
        layer = 'bn_edge',
        columns = ['m_length', 'from_node_object_id', 'to_node_object_id', 'basetype', 'geometry'],
    )  # takes ages to load
    .query('basetype == 2 or basetype == 6')  # only rail network
    .drop(columns = 'basetype')
    .sort_values(by = 'm_length')
    .drop_duplicates(  # around 40 dropped segments that are not unique based on start-end
        subset = ['from_node_object_id', 'to_node_object_id'],
        keep = 'first',
    )
    .set_index(['from_node_object_id', 'to_node_object_id'])
)

gdf_kn = (  # schienennetz knoten
    gpd
    .read_file(
        filename = 'https://data.geo.admin.ch/ch.swisstopo.swisstne-base/swisstne-base_2025-03-05/swisstne-base_2025-03-05_swisstnebase_2056_5728.gpkg.zip',
        layer = 'bn_node',
        columns = ['object_id', 'geometry'],
    )
    .set_index('object_id')
)
gdf_kn = gdf_kn.loc[  # only nodes that are the start or end of a railway edge
    (gdf_kn.index.isin(gdf_ka.index.get_level_values('from_node_object_id')))
    | (gdf_kn.index.isin(gdf_ka.index.get_level_values('to_node_object_id')))
]

### need to add two missing connections, between two points close to Wollishofen,
### and two points close to Reichenau-Bonaduz
wollishofen_line = shapely.LineString(
    [
        gdf_kn.loc['7dc1de4a-0d99-45b4-a148-16c0c85a4be2', 'geometry'],
        gdf_kn.loc['4fcd2c41-6dc6-46cd-be98-6b6d3c824ea0', 'geometry'],
    ]
)
reichenau_line = shapely.LineString(
    [
        gdf_kn.loc['c2533fbd-78da-4ead-92e4-12c41676c47d', 'geometry'],
        gdf_kn.loc['5ce3edab-8b7d-433f-936f-d1c11466defd', 'geometry'],
    ]
)
gdf_ka.loc[('7dc1de4a-0d99-45b4-a148-16c0c85a4be2', '4fcd2c41-6dc6-46cd-be98-6b6d3c824ea0'), :] = [wollishofen_line.length, wollishofen_line]
gdf_ka.loc[('c2533fbd-78da-4ead-92e4-12c41676c47d', '5ce3edab-8b7d-433f-936f-d1c11466defd'), :] = [reichenau_line.length, reichenau_line]

gdf_ka.to_file(cd.parent / 'assets' / 'schienennetz_kanten.geojson')
gdf_kn.to_file(cd.parent / 'assets' / 'schienennetz_knoten.geojson')
