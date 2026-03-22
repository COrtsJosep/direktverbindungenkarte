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
        
        for ds_id in self.__gdf_ds.index:  # take all nodes in a 250m radius from the station
            ds_p = self.__gdf_ds.loc[ds_id, 'geometry']
            distances = self.__gdf_kn.loc[:, 'geometry'].apply(lambda kn_p: kn_p.distance(ds_p))
            kn_in_circle = distances[distances <= 250].index
            for kn_id in kn_in_circle:  # add an artificial connection to each of those nodes
                kn_p = self.__gdf_kn.loc[kn_id, 'geometry']
                connection = shapely.LineString((ds_p, shapely.Point((kn_p.x, kn_p.y))))
                self.__gdf_ka.loc[
                    (ds_id, kn_id),
                    ['m_length', 'geometry']
                ] = [connection.length, connection]
                    
    
        self.__G = nx.Graph()
        for (node_from, node_to), row in self.__gdf_ka.iterrows():
            m_length = row['m_length']
            self.__G.add_edge(node_from, node_to, weight = m_length)

        self.__gdf_ka.to_crs('EPSG:4326', inplace = True)
        self.__gdf_kn.to_crs('EPSG:4326', inplace = True)
        self.__gdf_ds.to_crs('EPSG:4326', inplace = True)

    def get_linestring_route(self, number_start: str, number_end: str) -> set[shapely.LineString]:
        try:
            path_nodes = nx.shortest_path(self.__G, number_start, number_end)
        except (nx.NetworkXNoPath, nx.NodeNotFound):
            # there is no path between nodes or stations have no nodes nearby
            print(f'No path found between {number_start} and {number_end}.')
            return {  # just return a straight line between the 
                shapely.LineString(
                    [
                        self.__gdf_ds.loc[number_start, 'geometry'],
                        self.__gdf_ds.loc[number_end, 'geometry'],
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
