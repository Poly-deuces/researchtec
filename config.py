from dataclasses import dataclass

@dataclass
class RegionSpec:
    name: str
    lat_min: float
    lat_max: float
    lon_min: float
    lon_max: float
    use_mask: bool = False 
 
 