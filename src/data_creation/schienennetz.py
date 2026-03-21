import shapely
import networkx as nx
import geopandas as gpd
from pathlib import Path
cd = Path(__file__).parent

class SchienenNetz():
    def __init__(self):
        self.__gdf_ka = (
            gpd
            .read_file(cd.parent / 'assets' / 'schienennetz_kanten.geojson')
            .set_index(['from_node_object_id', 'to_node_object_id'])
        )
        self.__gdf_kn = (
            gpd
            .read_file(cd.parent / 'assets' / 'schienennetz_knoten.geojson')
            .set_index('object_id')
        )
        self.__gdf_ds = (
            gpd.read_file(cd.parent / 'assets' / 'dienststellen.geojson')
            .to_crs(self.__gdf_kn.crs)
            .set_index('number')
        )
        
        self.__cw = {}  # cw: crosswalk
        for ds_id in self.__gdf_ds.index:
            ds_p = self.__gdf_ds.loc[ds_id, 'geometry']
            distances = self.__gdf_kn.loc[:, 'geometry'].apply(lambda kn_p: kn_p.distance(ds_p))
            kn_in_circle = distances[distances <= 250].index.to_list()
            if kn_in_circle:
                self.__cw[ds_id] = kn_in_circle
    
        self.__G = nx.Graph()
        for (node_from, node_to), row in self.__gdf_ka.iterrows():
            m_length = row['m_length']
            self.__G.add_edge(node_from, node_to, weight = m_length)

        self.__gdf_ka.to_crs('EPSG:4326', inplace = True)
        self.__gdf_kn.to_crs('EPSG:4326', inplace = True)
        self.__gdf_ds.to_crs('EPSG:4326', inplace = True)

    def get_linestring_route(self, number_start: str, number_end: str) -> set[shapely.LineString]:
        if (  # station does not have a node at less than 250m
            (number_start not in self.__cw.keys()) 
            or (number_end not in self.__cw.keys())
        ):  # then just draw a straing line connecting the stations
            return {
                shapely.LineString(
                    [
                        self.__gdf_ds.loc[number_start, 'geometry'],
                        self.__gdf_ds.loc[number_end, 'geometry'],
                    ]
                ), 
            }
        
        path_nodes = []
        for node_start in self.__cw[number_start]:
            for node_end in self.__cw[number_end]:
                try:
                    path_nodes = nx.shortest_path(self.__G, node_start, node_end)
                except nx.NetworkXNoPath:
                    pass
                    
        if not path_nodes:  # somehow there is no path
            print(f'No path found between {number_start} and {number_end}.')
            return {  # just return a straight line between the nodes
                shapely.LineString(
                    [
                        self.__gdf_kn.loc[node_start, 'geometry'],
                        self.__gdf_kn.loc[node_end, 'geometry'],
                    ]
                ), 
            }
        
        # now just create the route by joining all segments
        linestring_route = set()
        for i in range(len(path_nodes) - 1):
            if (path_nodes[i], path_nodes[i + 1]) in self.__gdf_ka.index:
                key = (path_nodes[i], path_nodes[i + 1])
            else:
                key = (path_nodes[i + 1], path_nodes[i])
            
            linestring_route.add(
                self.__gdf_ka.loc[key, 'geometry']
            )
            
        return linestring_route
    
        

'''  # follows: code to check the quality of the crosswalk
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
'''
