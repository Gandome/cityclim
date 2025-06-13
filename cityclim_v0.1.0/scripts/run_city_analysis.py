from cityclim import load_city_polygons, load_climate_data, kelvin_humidity_convert, compute_city_stats

file_gpkg = "/path/to/cities.gpkg"
data_file = "/path/to/data.nc"
target_cities = ["Paris", "Berlin", "Rome"]
variable = "tas"

Time_period = ['daily', 'monthly', 'seasonal']
for time_scale in Time_period:
    time_period = time_scale
    plot_dir = "city_plots"
    output_csv = f"city_temperature_statistics_{time_period}.csv"

    # Load data
    cities_gdf = load_city_polygons(file_gpkg, target_names=target_cities)
    data, var_data = load_climate_data(data_file, variable)
    data = kelvin_humidity_convert(data, variable)
    var_data = data[variable]

    lon2d = data["lon"].values
    lat2d = data["lat"].values

    df = compute_city_stats(
        cities_gdf, var_data, lon2d, lat2d, variable,
        plot_dir=plot_dir, time_period=time_period,
        output_csv=output_csv
    )

