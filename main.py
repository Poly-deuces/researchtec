#%%
import xarray as xr
import numpy as np
import pandas as pd
import scipy.stats as stats
import matplotlib.pyplot as plt
import matplotlib.cm as cm
import cartopy.crs as ccrs
import cartopy.feature as cfeature
from pathlib import Path

#%%
basedir = Path(__file__).parent
tec_path = basedir/"data"/"tec"/"12_year_avg.nc"
csv_path = basedir/"data"/"solar_proxies"/"cls_radio_flux_f30.csv"
output_path=basedir/"results"

ds = xr.open_dataset(tec_path, engine="netcdf4")
tec = ds["atec"].transpose("time", "lat", "lon")
tec_years = ds["time"].dt.year.values

df = pd.read_csv(csv_path)
df.columns = [c.strip() for c in df.columns]
date_col = df.columns[0]
f30_col  = df.columns[1]
df["date"] = pd.to_datetime(df[date_col].astype(str).str.strip(), format="%Y %m %d")
df["f30"] = pd.to_numeric(df[f30_col], errors="coerce")

print("stop here")


#%%
# annual mean F30
df["year"] = df["date"].dt.year
f30_annual = df.groupby("year", as_index=False)["f30"].mean()

# merge with tec_years 
tec_year_df = pd.DataFrame({"year": tec_years})
merged = tec_year_df.merge(f30_annual, on="year", how="left")
f30_values = merged["f30"].values.astype(float)

#%%
# cos(latitude)
weights = np.cos(np.deg2rad(ds["lat"]))
weights.name = "weights"

# yearly mean TEC weighted by cos(latitude)
global_mean_tec = tec.weighted(weights).mean(dim=("lat", "lon"))

#%%
# r and r^2
tec_values = global_mean_tec.values.astype(float)
proxy_values = f30_values.astype(float)

mask = np.isfinite(tec_values) & np.isfinite(proxy_values)

r = np.corrcoef(tec_values[mask], proxy_values[mask])[0, 1]
r2 = r ** 2

print("r  =", r)
print("r² =", r2)

#%%
#double-step method
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


#trend map
nlat = tec.sizes["lat"]
nlon = tec.sizes["lon"]

trend_map = np.full((nlat, nlon), np.nan, dtype=float)

for i in range(nlat):
    for j in range(nlon):
        #if i % 10 == 0:
            #print(f"Processing lat index {i}/{nlat}...")
        tec_series = tec[:, i, j].values
        trend_map[i, j] = compute_beta(tec_series, f30_values, years)


trend_da = xr.DataArray(
    trend_map,
    coords={"lat": tec["lat"], "lon": tec["lon"]},
    dims=("lat", "lon"),
    name="trend"
)

cmap=cm.get_cmap("coolwarm").copy()
cmap.set_bad((0,0,0,0))

fig2_global=plt.figure(figsize=(12, 5))
ax=plt.axes(projection=ccrs.Mollweide())
ax.add_feature(cfeature.LAND, facecolor="lightgray", zorder=0)
ax.add_feature(cfeature.OCEAN, facecolor="lightblue", zorder=0)

trend_da.plot(
    ax=ax,
    transform=ccrs.PlateCarree(),
    x="lon",
    y="lat",
    cmap=cmap,
    robust=True,
    cbar_kwargs={"label": "Trend [TECU/year]","shrink": 0.8}
)

ax.coastlines()
ax.set_title("TEC trend at 12 LT (2000–2024), using F30 as solar proxy")

fig2_global.savefig(output_path/"fig2_global.png",dpi=300, bbox_inches="tight")
plt.tight_layout()
plt.show(block=True)

#histogram
trend_values = trend_da.values[np.isfinite(trend_da.values)]

mean_trend = np.mean(trend_values)
std_trend = np.std(trend_values)

print("Mean trend =", mean_trend)
print("Std trend  =", std_trend)
print("Valid grid count =", len(trend_values))

fig2_trend=plt.figure(figsize=(8, 5))

plt.hist(trend_values, bins=200, density=True)

plt.axvline(mean_trend,color="black", linestyle="--", label="Mean")
plt.axvline(0, color="black", linestyle="-")

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

plt.xlim(-0.8,0.6)
plt.xticks(np.arange(-0.8,0.6,0.2))
plt.ylim(0,5)
plt.yticks(np.arange(0,5,1))
fig2_trend.savefig(output_path/"fig2_trend.png",dpi=300, bbox_inches="tight")
plt.tight_layout()
plt.show(block=True)

# %%
