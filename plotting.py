import numpy as np
import matplotlib.pyplot as plt
import matplotlib.cm as cm
import cartopy.crs as ccrs
import cartopy.feature as cfeature


def plot_trend_map(trend_da, output_path,lt, proxy,region_name):
    cmap = cm.get_cmap("coolwarm").copy()
    cmap.set_bad((0, 0, 0, 0))

    fig2_trend = plt.figure(figsize=(12, 5))
    ax = plt.axes(projection=ccrs.PlateCarree())
    ax.add_feature(cfeature.LAND, facecolor="gray", zorder=0)
    ax.add_feature(cfeature.OCEAN, facecolor="lightblue", zorder=0)

    trend_da.plot(
        ax=ax,
        transform=ccrs.PlateCarree(),
        x="lon",
        y="lat",
        cmap=cmap,
        robust=True,
        cbar_kwargs={"label": "Trend [TECU/year]", "shrink": 0.8}
    )

    ax.coastlines()
    ax.set_title(f"{region_name} TEC trend at {lt} (2000–2024), using {proxy} as solar proxy")

    fig2_trend.savefig(output_path / f"{region_name} long term trend_{lt}_{proxy}.png", dpi=300, bbox_inches="tight")
    plt.close(fig2_trend)


def plot_histogram(trend_da, output_path,lt, proxy,region_name):
    trend_values = trend_da.values[np.isfinite(trend_da.values)]

    mean_trend = np.mean(trend_values)
    std_trend = np.std(trend_values)
    fig2_histogram = plt.figure(figsize=(8, 5))

    plt.hist(trend_values, bins="auto", density=True)

    plt.axvline(mean_trend, color="black", linestyle="--", label="Mean")
    plt.axvline(0, color="black", linestyle="-")

    plt.xlabel("Trend [TECU/year]")
    plt.ylabel("Density")
    plt.title(f"{region_name} Trend distribution at {lt} (2000–2024), using {proxy} as solar proxy")
    plt.legend()

    plt.text(
        0.05, 0.95,
        f"Mean: {mean_trend:.3f} TECU\nStd: {std_trend:.3f} TECU",
        transform=plt.gca().transAxes,
        va="top"
    )


    fig2_histogram.savefig(output_path / f"{region_name} trend histogram_{lt}_{proxy}.png", dpi=300, bbox_inches="tight")
    plt.close(fig2_histogram)
