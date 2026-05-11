import pandas as pd
from math import radians, sin, cos, sqrt, atan2

# Centro de Madrid: Puerta del Sol
SOL_LAT = 40.41694291608847
SOL_LON = -3.7035240891579964

def haversine_m(lat1, lon1, lat2, lon2):
    """
    Calcula distancia entre dos puntos GPS en metros.
    """
    R = 6371000  # radio medio de la Tierra en metros

    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])

    dlat = lat2 - lat1
    dlon = lon2 - lon1

    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))

    return R * c


# Leer CSV
# Cambia "ubicaciones.csv" por el nombre de tu archivo
df = pd.read_csv(
    "CasasEnVenta_Madrid_DistanciaSol.csv",
    sep=";",          # cambia a "," si tu CSV usa coma como separador de columnas
    decimal=","
)

# Asegurar nombres esperados
# Columnas esperadas: ID, latitud, longitud
df["distancia_metros_sol"] = df.apply(
    lambda row: haversine_m(
        row["latitud"],
        row["longitud"],
        SOL_LAT,
        SOL_LON
    ),
    axis=1
)

# Opcional: redondear a 2 decimales
df["distancia_metros_sol"] = df["distancia_metros_sol"].round(2)

# Guardar resultado
df.to_csv(
    "ubicaciones_con_distancia.csv",
    sep=";",
    decimal=",",
    index=False
)

print("Archivo generado: ubicaciones_con_distancia.csv")