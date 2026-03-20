import networkx as nx

gdf_edges = gpd.read_file('swisstne-base_2025-03-05_swisstnebase_2056_5728.gpkg.zip', layer = 'bn_edge')  # takes ages to load
gdf_edges.loc[gdf_edges.loc[:, 'basetype'] == 2].to_file('schienennetz.geojson', driver = 'GeoJSON')
gdf_railedges = (
    gpd
    .read_file(
        filename = 'schienennetz.geojson',
        columns = ['object_id', 'm_length', 'from_node_object_id', 'to_node_object_id', 'geometry']
    )
    .set_index('object_id')
    .sort_values(by = 'm_length')
    .drop_duplicates(  # around 40 dropped segments that are not unique based on start-end
        subset = ['from_node_object_id', 'to_node_object_id'],
        keep = 'first',
    )
    .set_index(['from_node_object_id', 'to_node_object_id'])
)

gdf_nodes = (
    gpd
    .read_file(
        'swisstne-base_2025-03-05_swisstnebase_2056_5728.gpkg.zip',
        layer = 'bn_node',
        columns = ['object_id', 'geometry'],
    )
    .set_index('object_id')
)
gdf_railnodes = gdf_nodes.loc[
    (gdf_nodes.index.isin(gdf_railedges.loc[:, 'from_node_object_id']))
    | (gdf_nodes.index.isin(gdf_railedges.loc[:, 'to_node_object_id']))
]








df_crosswalk = (
    gdf_railnodes
    .sjoin_nearest(
        right = gdf_ds.to_crs('EPSG:2056'),
        how = 'right',
        max_distance = 250 #53.415,  # tbd
        #distance_col = 'join_distance',
    )
    .dropna()
    .reset_index()
    .loc[:, ['number', 'object_id']]
)

df_crosswalk_no = df_crosswalk.set_index('number')
df_crosswalk_on = df_crosswalk.set_index('object_id')

G = nx.Graph()
for _, row in gdf_railedges.iterrows():
    node_from = row['from_node_object_id']
    node_to = row['to_node_object_id']
    m_length = row['m_length']
    
    G.add_edge(node_from, node_to, weight = m_length)


def get_linestring_route(number_start, number_end):
    node_start = df_crosswalk_no.loc[number_start, 'object_id']
    node_end = df_crosswalk_no.loc[number_end, 'object_id']
    
    path_nodes = nx.shortest_path(G, node_start, node_end)
    
    linestring_route = set()
    for i in range(len(path_nodes) - 1):
        if (path_nodes[i], path_nodes[i + 1]) in gdf_railedges.index:
           key = (path_nodes[i], path_nodes[i + 1])
        else:
            key = (path_nodes[i + 1], path_nodes[i])
        
        linestring_route.add(
            gdf_railedges.loc[key, 'geometry']
        )
        
    return linestring_route
    
        



lines = []
for station_id in j.index:
    node_id = j.loc[station_id, 'object_id']
    p = gdf_railnodes.loc[node_id, 'geometry']
    line = shapely.LineString(
        [
            gdf_ds.to_crs('EPSG:2056').loc[station_id, 'geometry'], 
            shapely.Point(p.x, p.y),
        ]
    )
    lines.append(line)

m = gpd.GeoDataFrame(data = {'object_id': j['object_id'], 'station_id': j.index, 'geometry': lines}, crs = 'EPSG:2056').explore()

folium.GeoJson(
    gdf_ds.to_crs('EPSG:2056'),
    name = 'Stations',
    tooltip = folium.GeoJsonTooltip(fields = ['designationOfficial']),
    marker = folium.Circle(radius = 100, fill_color = 'red', color = 'black')
).add_to(m)

folium.GeoJson(
    gdf_railnodes,
    name = 'Nodes',
    marker = folium.Circle(radius = 100, fill_color = 'blue', color = 'black')
).add_to(m)

m.save('comparison.html')
