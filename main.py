#%%
import xarray as xr
import numpy as np
import pandas as pd
import scipy.stats as stats
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
from pathlib import Path

#%%
basedir = Path(__file__).parent/"data"
tec_path = basedir/"tec"/"12_year_avg.nc"
ds = xr.open_dataset(tec_path, engine="netcdf4")
tec = ds["atec"].transpose("time", "lat", "lon")
print(ds)
tec_years = ds["time"].dt.year.values
print("TEC years:", tec_years)

csv_path = basedir/"solar_proxies"/"cls_radio_flux_f30.csv"
df = pd.read_csv(csv_path)


print("\n=== RAW CSV HEAD ===")
print(df.head())
print("\n=== RAW CSV COLUMNS ===")
print(df.columns.tolist())


date_col = df.columns[0]
f30_col  = df.columns[1]


df.columns = [c.strip() for c in df.columns]
date_col = df.columns[0]
f30_col  = df.columns[1]

df["date"] = pd.to_datetime(df[date_col].astype(str).str.strip(), format="%Y %m %d")

# 数值列转成 float
df["f30"] = pd.to_numeric(df[f30_col], errors="coerce")

print("\n=== PARSED HEAD ===")
print(df[["date", "f30"]].head())


#%%
# =========================
# 3. 按年份求 annual mean F30
# =========================
df["year"] = df["date"].dt.year

f30_annual = df.groupby("year", as_index=False)["f30"].mean()

print("\n=== ANNUAL F30 ===")
print(f30_annual.head())
print(f30_annual.tail())

#%%
# =========================
# 4. 和 TEC 年份对齐
# =========================
tec_year_df = pd.DataFrame({"year": tec_years})
merged = tec_year_df.merge(f30_annual, on="year", how="left")

print("\n=== MERGED YEARS ===")
print(merged)

f30_values = merged["f30"].values.astype(float)

print("\n=== FINAL F30 VALUES ===")
print(f30_values)
print("length =", len(f30_values))

# 检查有没有缺失
print("NaN count in annual F30:", np.isnan(f30_values).sum())
print(len(tec_years), len(f30_values))

# 5. 先画一下 annual F30 时间序列

plt.figure(figsize=(8, 4))
plt.plot(merged["year"], merged["f30"], marker="o")
plt.xlabel("Year")
plt.ylabel("Annual mean F30 (SFU)")
plt.title("Annual mean corrected F30")
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.show()

#%%
# 纬度权重：cos(latitude)
weights = np.cos(np.deg2rad(ds["lat"]))
weights.name = "weights"

# 加权全球平均，自动按 time 保留成一条年序列
global_mean_tec = tec.weighted(weights).mean(dim=("lat", "lon"))

print("\n=== GLOBAL MEAN TEC ===")
print(global_mean_tec)
print("shape =", global_mean_tec.shape)
print("values =", global_mean_tec.values)

# =========================
# 6. 计算 r 和 r^2
# =========================
tec_values = global_mean_tec.values.astype(float)
proxy_values = f30_values.astype(float)

mask = np.isfinite(tec_values) & np.isfinite(proxy_values)

r = np.corrcoef(tec_values[mask], proxy_values[mask])[0, 1]
r2 = r ** 2

print("\n=== CORRELATION ===")
print("r  =", r)
print("r² =", r2)

#%%
# 6. Figure 2: double-step trend using F30
years = tec_years.astype(float)

def compute_beta(tec_series, proxy_series, year_series):
    """
    tec_series   : 1D array, TEC at one grid point across years
    proxy_series : 1D array, annual F30 across years
    year_series  : 1D array, years
    return       : beta in TECU/year
    """
    mask = np.isfinite(tec_series) & np.isfinite(proxy_series) & np.isfinite(year_series)

    if mask.sum() != len(year_series):
        return np.nan
   #if mask.sum() < 10:
        #return np.nan

    tec_valid = tec_series[mask]
    proxy_valid = proxy_series[mask]
    year_valid = year_series[mask]

    # Step 1: TEC ~ F30
    # tec = b1 * proxy + a1
    b1, a1 = np.polyfit(proxy_valid, tec_valid, 1)
    tec_fit = b1 * proxy_valid + a1

    # residual
    residual = tec_valid - tec_fit

    # Step 2: residual ~ year
    # residual = beta * year + alpha
    beta, alpha = np.polyfit(year_valid, residual, 1)

    return beta

nlat = tec.sizes["lat"]
nlon = tec.sizes["lon"]

trend_map = np.full((nlat, nlon), np.nan, dtype=float)

for i in range(nlat):
    for j in range(nlon):
        if i % 10 == 0:
            print(f"Processing lat index {i}/{nlat}...")
        tec_series = tec[:, i, j].values
        trend_map[i, j] = compute_beta(tec_series, f30_values, years)


trend_da = xr.DataArray(
    trend_map,
    coords={"lat": tec["lat"], "lon": tec["lon"]},
    dims=("lat", "lon"),
    name="trend"
)

print("\n=== TREND DATAARRAY ===")
print(trend_da)

# =========================
# 7. 画 trend map
# =========================
plt.figure(figsize=(12, 4))
trend_da.plot(
    x="lon",
    y="lat",
    cmap="coolwarm",
    robust=True
)
plt.title("TEC trend at 12 LT (2000–2024), using F30 as solar proxy")
plt.xlabel("Longitude")
plt.ylabel("Latitude")
plt.tight_layout()
plt.show()

# 8. 画 histogram
trend_values = trend_da.values[np.isfinite(trend_da.values)]

mean_trend = np.mean(trend_values)
std_trend = np.std(trend_values)

print("\n=== HISTOGRAM STATS ===")
print("Mean trend =", mean_trend)
print("Std trend  =", std_trend)
print("Valid grid count =", len(trend_values))

plt.figure(figsize=(8, 5))
plt.hist(trend_values, bins=80, density=True)
plt.axvline(mean_trend, linestyle="--", label="Mean")
plt.xlabel("Trend [TECU/year]")
plt.ylabel("Density")
plt.title("Trend 12 LT")
plt.legend()
plt.text(
    0.05, 0.95,
    f"Mean: {mean_trend:.3f} TECU\nStd: {std_trend:.3f} TECU",
    transform=plt.gca().transAxes,
    va="top"
)
plt.tight_layout()
plt.show()

# %%
