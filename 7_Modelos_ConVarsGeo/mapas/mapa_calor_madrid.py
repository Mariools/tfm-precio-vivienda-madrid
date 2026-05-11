import argparse
import pandas as pd
import geopandas as gpd
import folium
import branca.colormap as cm
from shapely.geometry import Polygon


# =========================
# CONFIGURACIÓN DE COLORES
# =========================

COLD_HOT_COLORS = [
    "#2c7bb6",  # azul oscuro (muy bajo)
    "#74add1",  # azul medio
    "#abd9e9",  # azul claro
    "#ffffbf",  # amarillo (medio)
    "#fdae61",  # naranja claro
    "#f46d43",  # naranja fuerte
    "#d7191c"   # rojo (muy alto)
]


# =========================
# GEOHASH → POLÍGONO
# =========================

def geohash_to_polygon(geohash_value):
    import geohash2

    lat, lon, lat_err, lon_err = geohash2.decode_exactly(geohash_value)

    return Polygon([
        (lon - lon_err, lat - lat_err),
        (lon - lon_err, lat + lat_err),
        (lon + lon_err, lat + lat_err),
        (lon + lon_err, lat - lat_err),
        (lon - lon_err, lat - lat_err)
    ])


# =========================
# CREAR GEODATAFRAME
# =========================

def crear_gdf_desde_geohash(csv_path, geohash_col):
    df = pd.read_csv(csv_path, sep=";", decimal=".")

    df[geohash_col] = df[geohash_col].astype(str)
    df["geometry"] = df[geohash_col].apply(geohash_to_polygon)

    gdf = gpd.GeoDataFrame(
        df,
        geometry="geometry",
        crs="EPSG:4326"
    )

    return gdf


def crear_gdf_desde_codigo_postal(
    csv_path,
    geojson_path,
    csv_key,
    geojson_key
):

    df = pd.read_csv(csv_path, sep=";", decimal=".")
    gdf = gpd.read_file(geojson_path)

    df[csv_key] = df[csv_key].astype(str)
    gdf[geojson_key] = gdf[geojson_key].astype(str)

    gdf = gdf.merge(
        df,
        left_on=geojson_key,
        right_on=csv_key,
        how="inner"
    )

    gdf = gdf.to_crs(epsg=4326)

    return gdf


# =========================
# MAPA
# =========================

def crear_mapa_interactivo(
    gdf,
    id_col,
    variables,
    output_html,
    centro=(40.4168, -3.7038),
    zoom=10
):
    mapa = folium.Map(
        location=centro,
        zoom_start=zoom,
        tiles="CartoDB Positron"
    )



    for variable in variables:
        if variable not in gdf.columns:
            print(f"⚠️ Variable no encontrada: {variable}")
            continue

        valores = pd.to_numeric(gdf[variable], errors="coerce")
        gdf[variable] = valores

        valores_validos = valores.dropna()

        if valores_validos.empty:
            print(f"⚠️ Variable sin valores válidos: {variable}")
            continue

        breaks = valores_validos.quantile([
                        0.00, 0.20, 0.35, 0.50, 0.65, 0.80, 0.95
                ]).tolist()

        def style_function(feature, variable=variable, breaks=breaks):
            valor = feature["properties"].get(variable)

            if valor is None or pd.isna(valor):
                color = "#cccccc"
                fill_opacity = 0.15
            else:
                try:
                    valor = float(valor)

                    if valor <= breaks[1]:
                        color = COLD_HOT_COLORS[0]
                    elif valor <= breaks[2]:
                        color = COLD_HOT_COLORS[1]
                    elif valor <= breaks[3]:
                        color = COLD_HOT_COLORS[2]
                    elif valor <= breaks[4]:
                        color = COLD_HOT_COLORS[3]
                    elif valor <= breaks[5]:
                        color = COLD_HOT_COLORS[4]
                    elif valor <= breaks[6]:
                        color = COLD_HOT_COLORS[5]
                    else:
                        color = COLD_HOT_COLORS[6]

                    fill_opacity = 0.75

                except Exception:
                    color = "#cccccc"
                    fill_opacity = 0.15

            return {
                "fillColor": color,
                "color": "#333333",
                "weight": 0.4,
                "fillOpacity": fill_opacity
            }

        tooltip_fields = [id_col, variable]
        tooltip_aliases = ["Zona:", f"{variable}:"]

        capa = folium.FeatureGroup(
            name=variable,
            show=False
        )

        folium.GeoJson(
            gdf,
            name=variable,
            style_function=style_function,
            tooltip=folium.GeoJsonTooltip(
                fields=tooltip_fields,
                aliases=tooltip_aliases,
                localize=True,
                sticky=True
            )
        ).add_to(capa)

        capa.add_to(mapa)
        #colormap.add_to(mapa)


    legend_html = """
                <div style="
                position: fixed; 
                bottom: 50px; left: 50px; width: 260px; height: 90px; 
                background-color: white; 
                border:2px solid grey; z-index:9999; font-size:14px;
                padding: 10px;
                ">
                <b>Leyenda</b><br>
                <div style="display: flex; height: 15px;">
                    <div style="flex:1; background:#2c7bb6;"></div>
                    <div style="flex:1; background:#74add1;"></div>
                    <div style="flex:1; background:#abd9e9;"></div>
                    <div style="flex:1; background:#ffffbf;"></div>
                    <div style="flex:1; background:#fdae61;"></div>
                    <div style="flex:1; background:#f46d43;"></div>
                    <div style="flex:1; background:#d7191c;"></div>
                </div>
                <div style="display:flex; justify-content: space-between;">
                    <span>Bajo</span>
                    <span>Medio</span>
                    <span>Alto</span>
                </div>
                </div>
                """
    
    mapa.get_root().html.add_child(folium.Element(legend_html))

    titulo_html = """
                <h3 style="
                position: fixed; 
                top: 6px; left: 50%; transform: translateX(-50%);
                z-index:9999;
                background-color: white;
                padding: 6px 10px;
                border: 2px solid grey;
                border-radius: 3px;
                font-size: 13px;
                ">
                EL PRECIO DE LA VIVIENDA EN MADRID
                </h3>
                """

    mapa.get_root().html.add_child(folium.Element(titulo_html))

    folium.Marker(
        location=[40.4168, -3.7038],
        tooltip="Puerta del Sol",
        icon=folium.DivIcon(html="""
            <div style="
                font-size:16px;
                color:#196f3d;
            ">
                <i class="fa fa-map-marker"></i>
            </div>
        """)
    ).add_to(mapa)

    folium.LayerControl(collapsed=False).add_to(mapa)

    mapa.save(output_html)

    print(f"✅ Mapa generado correctamente: {output_html}")


# =========================
# MAIN
# =========================

def main():
    parser = argparse.ArgumentParser(
        description="Crear mapas de calor interactivos para Madrid por código postal o geohash."
    )

    parser.add_argument(
        "--modo",
        required=True,
        choices=["geohash", "codigo_postal"],
        help="Modo de generación del mapa."
    )

    parser.add_argument(
        "--csv",
        required=True,
        help="Ruta del CSV con las variables."
    )

    parser.add_argument(
        "--variables",
        required=True,
        help="Variables numéricas separadas por ;. Ej: renta_media;casas_en_venta;precio_m2"
    )

    parser.add_argument(
        "--output",
        default="mapa_calor_madrid.html",
        help="Nombre del HTML de salida."
    )

    parser.add_argument(
        "--geohash_col",
        default="geohash",
        help="Nombre de la columna geohash en el CSV."
    )

    parser.add_argument(
        "--geojson",
        help="Ruta del GeoJSON de códigos postales."
    )

    parser.add_argument(
        "--csv_key",
        default="codigo_postal",
        help="Columna de código postal en el CSV."
    )

    parser.add_argument(
        "--geojson_key",
        default="codigo_postal",
        help="Columna de código postal en el GeoJSON."
    )

    args = parser.parse_args()

    variables = [v.strip() for v in args.variables.split(",")]

    if args.modo == "geohash":
        gdf = crear_gdf_desde_geohash(
            csv_path=args.csv,
            geohash_col=args.geohash_col
        )

        id_col = args.geohash_col

    else:
        if not args.geojson:
            raise ValueError(
                "Para modo codigo_postal necesitas indicar --geojson"
            )

        gdf = crear_gdf_desde_codigo_postal(
            csv_path=args.csv,
            geojson_path=args.geojson,
            csv_key=args.csv_key,
            geojson_key=args.geojson_key
        )

        id_col = args.geojson_key

    crear_mapa_interactivo(
        gdf=gdf,
        id_col=id_col,
        variables=variables,
        output_html=args.output
    )


if __name__ == "__main__":
    main()


"""
EJECUTAR GEOHASH

python mapa_calor_madrid.py \
  --modo geohash \
  --csv data_geohash.csv \
  --geohash_col geohash_6 \
  --variables  viviendas_en_venta,precio_venta_medio,metros_cuadrados_promedio,renta_media_hogar,distancia_centro_Madrid_promedio,pois_comunitarios_g,pois_BigBusiness_G\
  --output mapa_geohash.html
"""

"""
EJECUTAR GEOHASH - MUNICIPIO MADRID

python mapa_calor_madrid.py \
  --modo geohash \
  --csv data_geohash_municipio_madrid.csv \
  --geohash_col geohash_6 \
  --variables  viviendas_en_venta,precio_venta_medio,metros_cuadrados_promedio,renta_media_hogar,distancia_centro_Madrid_promedio,pois_comunitarios_g,pois_BigBusiness_G\
  --output mapa_geohash_municipio_madrid.html
"""

"""
EJECUTAR CODIGO POSTAL

python mapa_calor_madrid.py \
  --modo codigo_postal \
  --csv data_cp.csv \
  --geojson geo_postal_codes_simple_ES.geojson \
  --csv_key postal_code \
  --geojson_key code \
  --variables viviendas_en_venta,precio_venta_medio,poblacion_km2_CP,metros_cuadrados_promedio,renta_media_hogar,distancia_centro_Madrid_promedio,pois_comunitarios_g,pois_BigBusiness_G \
  --output mapa_cp.html
"""