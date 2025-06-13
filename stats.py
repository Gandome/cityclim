import numpy as np
import pandas as pd
import os
from shapely.geometry import Polygon
from tqdm import tqdm
from .utils import format_units


def build_grid_polygons(lon2d, lat2d):
    ny, nx = lon2d.shape
    cell_polys = np.empty((ny, nx), dtype=object)
    for j in range(ny - 1):
        for i in range(nx - 1):
            lon_corners = [lon2d[j, i], lon2d[j, i+1], lon2d[j+1, i+1], lon2d[j+1, i]]
            lat_corners = [lat2d[j, i], lat2d[j+1, i+1], lat2d[j+1, i], lat2d[j, i+1]]
            cell_polys[j, i] = Polygon(zip(lon_corners, lat_corners))
    return cell_polys

def group_time_data(var_data, period):
    if period == "daily":
        return var_data.resample(time="1D")
    elif period == "monthly":
        return var_data.resample(time="1MS")
    elif period == "seasonal":
        return var_data.resample(time="QS-DEC")
    else:
        raise ValueError("Invalid time period: choose from 'daily', 'monthly', 'seasonal'")


def compute_city_stats(cities_gdf, var_data, lon2d, lat2d, variable, plot_dir="plots",
                       time_period="seasonal", output_csv="city_statistics.csv"):
    
    ny, nx = lon2d.shape
    grid_polys = build_grid_polygons(lon2d, lat2d)
    os.makedirs(plot_dir, exist_ok=True)
    results = []

    time_groups = group_time_data(var_data, time_period)

    for idx, city in tqdm(cities_gdf.iterrows(), total=len(cities_gdf)):
        city_name = city['GC_UCN_MAI_2025']
        country = city['GC_CNT_GAD_2025']
        polygon = city['geometry'].buffer(0)

        if polygon.geom_type == "MultiPolygon":
            polygon = max(polygon.geoms, key=lambda a: a.area)

        frac_mask = np.zeros((ny, nx))
        for j in range(ny - 1):
            for i in range(nx - 1):
                cell_poly = grid_polys[j, i]
                if cell_poly and polygon.intersects(cell_poly):
                    inter = polygon.intersection(cell_poly)
                    frac = inter.area / cell_poly.area if cell_poly.area > 0 else 0
                    frac_mask[j, i] = frac

        if frac_mask.sum() == 0:
            print(f"Warning: {city_name} has no overlapping grid cells. Skipping.")
            continue

        rows, cols = np.where(frac_mask > 0)
        row_min, row_max = rows.min(), rows.max()
        col_min, col_max = cols.min(), cols.max()

        var_crop = var_data[:, row_min:row_max+1, col_min:col_max+1]
        frac_crop = frac_mask[row_min:row_max+1, col_min:col_max+1]

        for t_name, t_group in time_groups:
            vals = t_group[:, row_min:row_max+1, col_min:col_max+1].mean(dim="time").values
            masked_vals = np.ma.masked_array(vals, mask=(frac_crop == 0))
            mean_val = np.ma.average(masked_vals, weights=frac_crop)
            median_val = np.ma.median(masked_vals)
            std_val = np.ma.std(masked_vals)
            min_val = masked_vals.min()
            max_val = masked_vals.max()
            n_cells = (frac_crop > 0).sum()
            total_weight = frac_crop.sum()
            units_raw = var_data.attrs.get("units", "")
            units_fmt = format_units(units_raw)

            results.append({
                "City": city_name,
                "Country": country,
                "Period": str(t_name),
                "Mean": round(mean_val, 2),
                "Median": round(median_val, 2),
                "Mean - Median": round(mean_val - median_val, 2),
                "Std": round(std_val, 2),
                "Min": round(min_val, 2),
                "Max": round(max_val, 2),
                "Unit": units_fmt,
                "GridCells": int(n_cells),
                "TotalWeight": round(total_weight, 2)
            })

    df = pd.DataFrame(results)
    df.to_csv(output_csv, index=False)
    print(f"\nSaved results to: {output_csv}")
    return df
