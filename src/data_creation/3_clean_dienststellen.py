import pandas as pd
import geopandas as gpd
from pathlib import Path
cd = Path(__file__).parent

# load dienststellen and ist-data
gdf_ds = gpd.read_file(cd.parent / 'assets' / 'dienststellen_dirty.geojson').set_index('number')
df_is = pd.read_json(cd.parent / 'assets' / 'istdaten.json', dtype = {'BPUIC': str})

# get served stations
served_ds = df_is.loc[:, 'BPUIC'].unique()

# filter and export
(
    gdf_ds
    .loc[gdf_ds.index.isin(served_ds)]
    .to_file(cd.parent / 'assets' / 'dienststellen.geojson')
)
