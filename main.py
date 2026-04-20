from pathlib import Path
import pandas as pd
import numpy as np

from data_processing import (
    load_tec_and_proxy,
    area_weighted_mean,
    compute_r,
    compute_beta,
    compute_trend_map,
    subset_region,
)
from config_settings import Greenland, lt_list, proxy_list
from plotting import plot_trend_map, plot_histogram, plot_regional_trend_map,plot_regional_histogram


def main():
    basedir = Path(__file__).parent
    output_path = basedir / "results"

    trend_summary={
        "proxy":[],
        "lt":[],
        "Greenland":[],
        "r":[],
        "r2":[],
        "std_trend":[],
        "mean_trend":[],
    }

    for proxy in proxy_list:
        for lt in lt_list:
            tec_path = basedir / "data" / "tec" / f"{lt}_year_avg.nc"   
            csv_path = basedir / "data" / "solar_proxies" / f"{proxy}.csv"
            tec, tec_years, proxy_values = load_tec_and_proxy(tec_path=tec_path, csv_path=csv_path)
            
            Greenland_mean_tec = area_weighted_mean(subset_region(tec, Greenland))
            Greenland_mean_tec_values = Greenland_mean_tec.values.astype(float)

            r, r2 = compute_r(Greenland_mean_tec_values, proxy_values=proxy_values)

            regions = {
                "Greenland": subset_region(tec, Greenland),
                }

            trend_results = {
                name: compute_trend_map(region_tec, proxy_values, tec_years)
                for name, region_tec in regions.items()
            }

            Greenland_trend_da = trend_results["Greenland"]
            Greenland_trend_mean=area_weighted_mean(trend_results["Greenland"])

            trend_values = Greenland_trend_da.values[np.isfinite(Greenland_trend_da.values)]

            mean_trend = np.mean(trend_values)
            std_trend = np.std(trend_values)
                    
            trend_summary["lt"].append(lt)
            #trend_summary["global"].append(float(global_trend_mean))
            trend_summary["Greenland"].append(float(Greenland_trend_mean))
            trend_summary["proxy"].append(proxy)
            trend_summary["r"].append(r)
            trend_summary["r2"].append(r2)
            trend_summary["std_trend"].append(std_trend)
            trend_summary["mean_trend"].append(mean_trend)

        trend_df=pd.DataFrame(trend_summary)
        trend_df.to_csv(output_path / "trend_summary.csv", index=False)

        print(trend_summary)

"""     
        plot_trend_map(trend_da, output_path)
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