from pathlib import Path
import pandas as pd
import numpy as np

from data_processing import (
    load_tec_and_proxy,
    prepare_region_tec,
    area_weighted_mean,
    compute_r,
    compute_beta,
    compute_trend_map,
    subset_region,
)
from config_settings import Greenland,Greenland_island, lt_list, proxy_list
from plotting import plot_trend_map, plot_histogram, plot_regional_trend_map,plot_regional_histogram


def main():
    basedir = Path(__file__).parent
    boudary_path = basedir / "data" / "Greenland_coast.shp"
    output_path = basedir / "results"

    trend_records = []

    for proxy in proxy_list:
        for lt in lt_list:
            tec_path = basedir / "data" / "tec" / f"{lt}_year_avg.nc"   
            csv_path = basedir / "data" / "solar_proxies" / f"{proxy}.csv"
            tec, tec_years, proxy_values = load_tec_and_proxy(tec_path=tec_path, csv_path=csv_path)

            regions = {
                "Greenland": Greenland,
                "Greenland_island": Greenland_island,
                }

            for region_name,region_tec in regions.items():
                region_tec = prepare_region_tec(tec=tec, region=regions[region_name], boundary_path=boudary_path)
                region_mean_tec = area_weighted_mean(region_tec)
                region_mean_tec_values = region_mean_tec.values.astype(float)
                r,r2 = compute_r(proxy_values, region_mean_tec_values)
                region_trend_da = compute_trend_map(region_tec, proxy_values, tec_years)
                region_trend_mean=area_weighted_mean(region_trend_da)

                trend_values = region_trend_da.values[np.isfinite(region_trend_da.values)]

                mean_trend = np.mean(trend_values)
                std_trend = np.std(trend_values)
                        
                trend_records.append({
                    "lt": lt,
                    "proxy": proxy,
                    "region": region_name,
                    "r": r,
                    "r2": r2,
                    "std_trend": std_trend,
                    "mean_trend": mean_trend
                })


            plot_trend_map(region_trend_da, output_path, lt, proxy, region_name)
            plot_histogram(region_trend_da, output_path, lt, proxy, region_name)

    trend_df=pd.DataFrame(trend_records)
    trend_df.to_csv(output_path / "trend_summary.csv", index=False)

    print(trend_records)



"""     
        plot_trend_map(trend_da, output_path, lt, proxy)
        plot_histogram(trend_da, output_path)
        plot_regional_trend_map(trend_results["iceland"], Greenland, output_path, "fig2_iceland.png", "Iceland")
        plot_regional_histogram(trend_results["iceland"], output_path, "fig2    iceland_histogram.png", "Iceland")
"""

"""
LT   global trend     Table S1 F30
0    -0.0282              -0.028
1    -0.0232              -0.023
2    -0.0146              -0.015
3    -0.0145              -0.015
4    -0.0209              -0.022
5    -0.0299              -0.031
6    -0.0458              -0.047
7    -0.0685              -0.070
8    -0.0862              -0.090
9    -0.0981              -0.100
10   -0.0961              -0.100
11   -0.1194              -0.120
12   -0.1201              -0.120
13   -0.1155              -0.120
14   -0.0819              -0.080
15   1.356e+21            -0.100
16   -0.0593              -0.060
17   -0.0814              -0.090
18   -0.0412              -0.040
19   -0.0591              -0.060
20   -0.0262              -0.030
21   -0.0404              -0.041
22   -0.0408              -0.042
23   -0.0337              -0.034
"""

if __name__ == "__main__":
    main()