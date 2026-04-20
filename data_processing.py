import xarray as xr
import numpy as np
import pandas as pd
import geopandas as gpd
from shapely import contains_xy

def load_tec_and_proxy(tec_path, csv_path):
    ds = xr.open_dataset(tec_path, engine="netcdf4")
    tec = ds["atec"].transpose("time", "lat", "lon")
    tec_years = ds["time"].dt.year.values

    df = pd.read_csv(csv_path)
    df.columns = [c.strip() for c in df.columns]
    date_col = df.columns[0]
    f30_col = df.columns[1]

    df["date"] = pd.to_datetime(
        df[date_col].astype(str).str.strip(),
        format="%Y %m %d"
    )
    df["proxy"] = pd.to_numeric(df[f30_col], errors="coerce")

    # annual mean F30
    df["year"] = df["date"].dt.year
    proxy_annual = df.groupby("year", as_index=False)["proxy"].mean()

    # merge with tec_years
    tec_year_df = pd.DataFrame({"year": tec_years})
    merged = tec_year_df.merge(proxy_annual, on="year", how="left")
    proxy_values = merged["proxy"].values.astype(float)

    return tec, tec_years, proxy_values

def build_greenland_mask(tec_box, boundary_path):
    """
    tec_box: 已经按矩形框裁切后的 DataArray, dims = (time, lat, lon)
    boundary_path: Greenland 边界文件路径（shp 或 geojson）
    return: mask_da, dims = (lat, lon), True 表示岛内
    """
    gdf = gpd.read_file(boundary_path)
    gdf = gdf.to_crs("EPSG:4326")

    # 如果文件里只有 Greenland 一个对象，直接 union
    # 如果有多行，也会合并成一个 polygon / multipolygon
    poly = gdf.geometry.union_all()

    # 生成网格点中心
    lon2d, lat2d = np.meshgrid(tec_box["lon"].values, tec_box["lat"].values)

    # 判断每个格点中心是否落在 polygon 内
    mask_np = contains_xy(poly, lon2d, lat2d)

    mask_da = xr.DataArray(
        mask_np,
        coords={"lat": tec_box["lat"], "lon": tec_box["lon"]},
        dims=("lat", "lon"),
        name="greenland_mask"
    )

    return mask_da

def prepare_region_tec(tec, region, boundary_path=None):
    region_tec = subset_region(tec, region)

    if region.use_mask:
        mask_da = build_greenland_mask(region_tec, boundary_path)
        region_tec = region_tec.where(mask_da)

    return region_tec

def area_weighted_mean(da):
    weights = np.cos(np.deg2rad(da["lat"]))
    weights.name = "weights"
    return da.weighted(weights).mean(dim=("lat", "lon"))


def compute_r(tec_values, proxy_values):
    mask = np.isfinite(tec_values) & np.isfinite(proxy_values)
    r = np.corrcoef(tec_values[mask], proxy_values[mask])[0, 1]
    r2 = r ** 2

    return r, r2


def compute_beta(tec_series, proxy_series, year_series):
    mask = np.isfinite(tec_series) & np.isfinite(proxy_series) & np.isfinite(year_series)

    if mask.sum() != len(year_series):
        return np.nan
    #if mask.sum() < 24:  # require at least 20 valid points to compute a reliable trend
        #return np.nan


    tec_valid = tec_series[mask]
    proxy_valid = proxy_series[mask]
    year_valid = year_series[mask]

    # Step 1: TEC ~ F30
    b1, a1 = np.polyfit(proxy_valid, tec_valid, 1)
    tec_fit = b1 * proxy_valid + a1

    # residual
    residual = tec_valid - tec_fit

    # Step 2: residual ~ year
    beta, alpha = np.polyfit(year_valid, residual, 1)

    return beta


def subset_region(tec,region):
    return tec.sel(lat=slice(region.lat_min, region.lat_max),
                   lon=slice(region.lon_min, region.lon_max))


def compute_trend_map(tec, proxy_values, tec_years):
    nlat = tec.sizes["lat"]
    nlon = tec.sizes["lon"]

    trend_map = np.full((nlat, nlon), np.nan, dtype=float)

    for i in range(nlat):
        for j in range(nlon):
            tec_series = tec[:, i, j].values
            trend_map[i, j] = compute_beta(tec_series, proxy_values, tec_years)

    trend_da = xr.DataArray(
        trend_map,
        coords={"lat": tec["lat"], "lon": tec["lon"]},
        dims=("lat", "lon"),
        name="trend"
    )

    return trend_da

