from pathlib import Path

from data_processing import (
    load_tec_and_proxy,
    area_weighted_mean,
    compute_r,
    compute_trend_map,
)
from plotting import plot_trend_map, plot_histogram


def main():
    basedir = Path(__file__).parent
    tec_path = basedir / "data" / "tec" / "12_year_avg.nc"
    csv_path = basedir / "data" / "solar_proxies" / "cls_radio_flux_f30.csv"
    output_path = basedir / "results"
    output_path.mkdir(parents=True, exist_ok=True)

    ds, tec, tec_years, f30_values = load_tec_and_proxy(tec_path, csv_path)

    global_mean_tec = area_weighted_mean(tec)
    tec_values = global_mean_tec.values.astype(float)
    proxy_values = f30_values.astype(float)

    r, r2 = compute_r(tec_values, proxy_values)

    print("r  =", r)
    print("r² =", r2)

    years = tec_years.astype(float)
    trend_da = compute_trend_map(tec, f30_values, years)

    plot_trend_map(trend_da, output_path)
    plot_histogram(trend_da, output_path)


if __name__ == "__main__":
    main()