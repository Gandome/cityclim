import xarray as xr

def load_climate_data(nc_file, variable):
    ds = xr.open_dataset(nc_file)
    return ds, ds[variable]

def kelvin_humidity_convert(ds, variable):
    units = ds[variable].attrs.get('units', '').lower()
    if units == 'k':
        ds[variable] = ds[variable] - 273.15
        ds[variable].attrs['units'] = 'degC'
    elif units == 'g/kg':
        ds[variable] = ds[variable] / 1000.0
        ds[variable].attrs['units'] = 'kg/kg'
    elif units == 'kg/kg':
        ds[variable] = ds[variable] * 1000.0
        ds[variable].attrs['units'] = 'g/kg'
    return ds
