import xarray as xr
import numpy as np
import pandas as pd


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
    df["f30"] = pd.to_numeric(df[f30_col], errors="coerce")

    # annual mean F30
    df["year"] = df["date"].dt.year
    f30_annual = df.groupby("year", as_index=False)["f30"].mean()

    # merge with tec_years
    tec_year_df = pd.DataFrame({"year": tec_years})
    merged = tec_year_df.merge(f30_annual, on="year", how="left")
    f30_values = merged["f30"].values.astype(float)

    return tec, tec_years, f30_values


def area_weighted_mean(da):
    weights = np.cos(np.deg2rad(da["lat"]))
    weights.name = "weights"
    return da.weighted(weights).mean(dim=("lat", "lon"))


def compute_r(tec_values, proxy_values):
    mask = np.isfinite(tec_values) & np.isfinite(proxy_values)
    r = np.corrcoef(tec_values[mask], proxy_values[mask])[0, 1]
    r2 = r ** 2
    print("r  =", r)
    print("r² =", r2)

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


def compute_trend_map(tec, f30_values, tec_years):
    nlat = tec.sizes["lat"]
    nlon = tec.sizes["lon"]

    trend_map = np.full((nlat, nlon), np.nan, dtype=float)

    for i in range(nlat):
        for j in range(nlon):
            tec_series = tec[:, i, j].values
            trend_map[i, j] = compute_beta(tec_series, f30_values, tec_years)

    trend_da = xr.DataArray(
        trend_map,
        coords={"lat": tec["lat"], "lon": tec["lon"]},
        dims=("lat", "lon"),
        name="trend"
    )

    return trend_da

