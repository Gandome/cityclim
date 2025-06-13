def format_units(units):
    units = units.lower()
    return {
        'degc': '°C',
        'k': 'K',
        'g/kg': 'gkg⁻¹',
        'kg/kg': 'kgkg⁻¹'
    }.get(units, units)
