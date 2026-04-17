from pathlib import Path

from data_processing import (
    load_tec_and_proxy,
    area_weighted_mean,
    compute_r,
    compute_beta,
    compute_trend_map,
    subset_region,
)
from config_settings import iceland, same_lat_band, global_region, cfg_12lt_f30
from plotting import plot_trend_map, plot_histogram, plot_regional_trend_map,plot_regional_histogram


def main():

    basedir = Path(__file__).parent
    tec_path = basedir / "data" / "tec" / "12_year_avg.nc"
    csv_path = basedir / "data" / "solar_proxies" / "cls_radio_flux_f30.csv"
    output_path = basedir / "results"

    tec, tec_years, f30_values = load_tec_and_proxy(tec_path, csv_path)

    global_mean_tec = area_weighted_mean(tec)
    tec_values = global_mean_tec.values.astype(float)

    r, r2 = compute_r(tec_values, proxy_values=f30_values)

    regions = {
        "global": tec,
        "iceland": subset_region(tec, iceland),
        "same_lat_band": subset_region(tec, same_lat_band),
    }

    trend_results = {
        name: compute_trend_map(region_tec, f30_values, tec_years)
        for name, region_tec in regions.items()
    }

    trend_da = trend_results["global"]

    plot_trend_map(trend_da, output_path)
    plot_histogram(trend_da, output_path)
    plot_regional_trend_map(trend_results["iceland"], iceland, output_path, "fig2_iceland.png", "Iceland")
    plot_regional_trend_map(trend_results["same_lat_band"], same_lat_band,  output_path, "fig2_same_lat_band.png", "Same Latitude Band")
    plot_regional_histogram(trend_results["iceland"], output_path, "fig2    iceland_histogram.png", "Iceland")
    plot_regional_histogram(trend_results["same_lat_band"], output_path, "fig2_same_lat_band_histogram.png", "Same Latitude Band")

if __name__ == "__main__":
    main()