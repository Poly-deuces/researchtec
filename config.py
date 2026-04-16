from dataclasses import dataclass

@dataclass
class RegionSpec:
    name: str
    lat_min: float
    lat_max: float
    lon_min: float
    lon_max: float
    

@dataclass
class AnalysisConfig:
    lt: int
    proxy_name: str = "F30" 
 