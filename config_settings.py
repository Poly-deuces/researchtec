from config import RegionSpec, AnalysisConfig

Greenland = RegionSpec(
    name="Greenland",
    lat_min=60.0,
    lat_max=84.0,
    lon_min=-74.0,
    lon_max=-11.0
)

lt_list=list(range(0,24))

proxy_list=["cls_radio_flux_f30","cls_radio_flux_f8","cls_radio_flux_f107","international_sunspot_number"]
