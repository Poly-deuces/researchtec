from config import RegionSpec, AnalysisConfig

iceland = RegionSpec(
    name="Iceland",
    lat_min=63.0,
    lat_max=67.0,
    lon_min=-25.0,
    lon_max=-13.0
)

same_lat_band = RegionSpec(
    name="Iceland_same_lat_band",
    lat_min=60.0,
    lat_max=90.0,
    lon_min=-180.0,
    lon_max=180.0
)

global_region = RegionSpec(
    name="Global",
    lat_min=-90.0,
    lat_max=90.0,
    lon_min=-180.0,
    lon_max=180.0
)

cfg_12lt_f30 = AnalysisConfig(
    lt=12,
    proxy_name="F30"
)

