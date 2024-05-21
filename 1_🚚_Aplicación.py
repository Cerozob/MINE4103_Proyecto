import streamlit as st
from streamlit import session_state as state
import st_on_hover_tabs as hovertabs
from pathlib import Path
import pandas as pd
import folium
import json
from streamlit_folium import st_folium
from sklearn.cluster import DBSCAN, KMeans
from sklearn.preprocessing import StandardScaler
from pages.utils import rules
from sklearn.metrics.pairwise import haversine_distances
import random
from numpy import radians


if "capacities" not in state:
    rules.load_all()


st.set_page_config(page_title="Página principal", page_icon="🏠")

bbox_samples = {"lon1": -74.257278, "lat1": 4.514137,
                "lon2": -74.031372, "lat2": 4.812523}

def human_format(num):
    num = float('{:.3g}'.format(num))
    magnitude = 0
    while abs(num) >= 1000:
        magnitude += 1
        num /= 1000.0
    return '{}{}'.format('{:f}'.format(num).rstrip('0').rstrip('.'), ['', 'K', 'M', 'B', 'T'][magnitude])

def randomize(dataframe):
    nsamples = 15
   
    productos_samples = ["Paracetamol", "Ibuprofeno", "Omeprazol"]
    dataframe["ID"] = [f"ID-{i}" for i in range(nsamples)]
    dataframe.set_index("ID", inplace=True)
    dataframe["Producto"] = [random.choice(
        productos_samples) for _ in range(nsamples)]
    dataframe["Cantidad"] = [random.randint(1, 1000) for _ in range(nsamples)]
    dataframe["lat"] = [random.uniform(
        bbox_samples["lat1"], bbox_samples["lat2"]) for _ in range(nsamples)]
    dataframe["lon"] = [random.uniform(
        bbox_samples["lon1"], bbox_samples["lon2"]) for _ in range(nsamples)]
    return dataframe


if "órdenes" not in state:
    state.órdenes = pd.read_csv("./assets/sample_file.csv")
    # remove nans or nulls and reset index
    state.órdenes = state.órdenes.dropna().reset_index(drop=True)
if state.órdenes.empty:
    state.órdenes = randomize(state.órdenes)




farmulogo_path = Path("./assets/farmu_logo.svg")
farmudots_path = Path("./assets/farmu_dots.svg")
bogotamap_path = Path("./assets/bogota_cadastral.json")

with open(bogotamap_path, "rt") as bog:
    bogotamap = json.load(bog)

with open(farmulogo_path, "rt") as logo, open(farmudots_path, "rt") as dots:
    farmulogo = logo.read()
    farmudots = dots.read()


_, col1, _ = st.columns([1, 3, 1])
col1.image(farmudots, use_column_width=True, output_format="SVG")
col1.image(farmulogo, use_column_width=True, output_format="SVG")

st.title("Estimación de envíos para órdenes Farmacéuticos")

st.write("Sube tu archivo de órdenes para estimar los envíos")
uploaded_file = st.file_uploader(
    "Sube tu archivo de órdenes", type=["csv", "xlsx"])

if uploaded_file is not None:

    st.write(f"Archivo subido: {uploaded_file.name}")
    file_dframe = pd.read_csv(uploaded_file) if uploaded_file.name.endswith(
        ".csv") else pd.read_excel(uploaded_file)
    state.órdenes = file_dframe
else:
    st.write("No se ha subido ningún archivo")

    st.write("No sabes en qué formato subir tu archivo?, descarga este ejemplo")
    with open("./assets/plantilla_pedidos.csv", "rb") as f:
        st.download_button("Descargar ejemplo en csv", f.read(), "plantilla_órdenes.csv", "text/csv")
    with open("./assets/plantilla_pedidos.xlsx", "rb") as f:
        st.download_button("Descargar ejemplo en xlsx", f.read(),"plantilla_órdenes.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

    st.write("También puedes ingresar tus órdenes manualmente si lo prefieres")
    state.órdenes = state.órdenes.drop(columns=["shopify_id"], errors="ignore") if "shopify_id" in state.órdenes else state.órdenes
    modificado_df = st.data_editor(state.órdenes, num_rows="dynamic")

    st.write("Una vez que hayas ingresado tus órdenes, presiona el botón de abajo para estimar los envíos")
    if st.button("Estimar envíos"):
        state.órdenes = modificado_df

if "órdenes" in state:
    state.órdenes = state.órdenes.drop(columns=["shopify_id"], errors="ignore") if "shopify_id" in state.órdenes else state.órdenes
    st.write(f"se han ingresado {human_format(state.órdenes['order_number'].nunique())} pedido/s con {human_format(state.órdenes.shape[0])} SKUs")
    state.órdenes["order_date"] = pd.to_datetime(state.órdenes["order_date"])
    # place 2 date pickers to filter the data
    st.write("## 0. Filtrar órdenes")
    st.write("Puedes filtrar los órdenes por fecha")
    date1 = st.date_input("Fecha de inicio", state.órdenes["order_date"].min())
    date2 = st.date_input("Fecha de fin", state.órdenes["order_date"].max())
    # pass both to pandas datetimes
    date1 = pd.to_datetime(date1)
    date2 = pd.to_datetime(date2)
    state.órdenes = state.órdenes[(state.órdenes["order_date"] >= date1) & (
        state.órdenes["order_date"] <= date2)]
    st.write(f"Se han filtrado {human_format(state.órdenes.shape[0])} órdenes")


    with st.spinner("Estimando envíos..."):
        st.write("## 1. Estimación de cantidad de cajas")
        notsueros = state.órdenes[state.órdenes["suero_condition"]==0]
        sueros = state.órdenes[state.órdenes["suero_condition"]==1]
        conteo_sueros = int(sueros["quantity"].sum())
        dimensiones = notsueros["width"]*notsueros["height"]*notsueros["depth"]*notsueros["quantity"]
        dimensiones = float(dimensiones.sum())
        print(f"se han estimado {human_format(dimensiones)} cm3")
        result1_sueros = rules.run_rules_boxes(
            conteo_sueros, num_boxes=0, num_products_out=0, is_sueros=True)
        result1_not_sueros = rules.run_rules_boxes(
            dimensiones, num_boxes=0, num_products_out=0, is_sueros=False)
        st.write(
            f"Resultado de sueros: Para {human_format(conteo_sueros)} sueros se necesitan {human_format(result1_sueros['num_boxes'])} cajas junto con {human_format(result1_sueros['num_boxes'])} cajas para sueros y {human_format(result1_sueros['num_products_out'])} productos individuales")
        st.write(
            f"Resultado de productos: Para {human_format(dimensiones)} cm3 se necesitan {human_format(result1_not_sueros['num_boxes'])} cajas junto con {human_format(result1_not_sueros['num_boxes'])} cajas")
    with st.spinner("Estimando cantidad de vehículos..."):
        st.write("## 2. Estimación de cantidad de vehículos")
        total_boxes = result1_sueros["num_boxes"] + result1_not_sueros["num_boxes"]
        result2 = rules.run_rules_truck(
            total_boxes, num_trucks=0, num_bikes=0)
        st.write(
            f"Resultado: Para {human_format(total_boxes)} cajas se necesitan {human_format(result2['num_trucks'])} carrys y {human_format(result2['num_bikes'])} motos")
    st.write("## 3. Envíos")
    with st.spinner("Estimando envíos"):
        mapa = folium.Map(location=[4.6458888888889, -74.0775], zoom_start=11)
        fg = folium.FeatureGroup(name="Ubicaciones de envíos")
        scaler = StandardScaler()
        colorchoices = ['red', 'blue', 'green', 'purple', 'orange', 'darkred', 'lightred', 'beige', 'darkblue',
                        'darkgreen', 'cadetblue', 'darkpurple', 'white', 'pink', 'lightblue', 'lightgreen', 'gray', 'black', 'lightgray']
        # clustering_model = DBSCAN(eps=0.25, min_samples=3,metric='haversine')
        # clustering_model.__name__ = "DBSCAN"
        totalvehicles = result2["num_trucks"] + result2["num_bikes"]
        clustering_model = KMeans(n_clusters=min(
            totalvehicles, state.órdenes.shape[0]))
        clustering_model.__name__ = "KMeans"
        
        state.órdenes[["lat_std", "lon_std"]] = scaler.fit_transform(
            state.órdenes[["latitude", "longitude"]])
        if "cluster" not in state.órdenes:
            state.órdenes["cluster"] = clustering_model.fit_predict(
                state.órdenes[["lat_std", "lon_std"]])
        st.write("Viajes estimados")
        nclusters = state.órdenes["cluster"].nunique()
        print(f"se han estimado {nclusters} envíos")
        for cluster in state.órdenes["cluster"].unique():
            cluster_df = state.órdenes[state.órdenes["cluster"] == cluster]
            cluster_fg = folium.FeatureGroup(name=f"Cluster {cluster}")
            for idx, pedido in cluster_df.iterrows():
                marker = folium.Marker(location=[pedido["latitude"], pedido["longitude"]],
                                       popup=f"{pedido['product_description']} - {human_format(pedido['quantity'])} unidades. Vehículo {cluster}",
                                       icon=folium.Icon(color=colorchoices[cluster % len(colorchoices)], icon="info-sign", icon_color="white"))
                cluster_fg.add_child(marker)
            mapa.add_child(cluster_fg)

        elmapa = st_folium(
            mapa, feature_group_to_add=cluster_fg, use_container_width=True)
        # state.origin = list(elmapa["last_clicked"].values()) if "last_clicked" in elmapa and elmapa["last_clicked"] is not None else [4.652148006033854, -74.11982593339519]
        state.origin = [4.652148006033854, -74.11982593339519]
        # it is lat lon format
        # calculate the distances from the origin to the clusters centers
        distances = {}
        for cluster in state.órdenes["cluster"].unique():
            cluster_df = state.órdenes[state.órdenes["cluster"] == cluster]
            cluster_center = cluster_df[["latitude", "longitude"]].mean().astype(float)
            # ids are not in cluster_df but in state.órdenes
            orders_ids = ", ".join(cluster_df["order_number"].astype(str))
            cluster_id = cluster_df["cluster"].iloc[0]
            # save the distance in km, also the ids of the orders in the cluster
            distances[cluster] = haversine_distances([radians(state.origin)], [radians(
                cluster_center)])[0][0] * 6371000/1000, orders_ids, cluster_id

        st.write("Distancias estimadas")
        # add the ids of the orders in the cluster
        distancesdataframe = pd.DataFrame(distances).T
        distancesdataframe.columns = ["Distancia (Km)", "órdenes", "Vehículo"]
        # proper python datatypes
        distancesdataframe["Distancia (Km)"] = distancesdataframe["Distancia (Km)"].astype(
            float)
        distancesdataframe["órdenes"] = distancesdataframe["órdenes"].astype(str)
        distancesdataframe["Vehículo"] = distancesdataframe["Vehículo"].astype(
            int)
        st.dataframe(distancesdataframe)
        distance = sum(distancesdataframe["Distancia (Km)"])
        result3 = rules.run_rules_delivery_cost(
            distance, num_trucks=result2["num_trucks"], num_bikes=result2["num_bikes"], total_value=0)
        st.write(
            f"Resultado: Para una distancia de {human_format(distance)} km, se necesitan {human_format(result3['total_value'])} pesos en costos de envío")

    # st.write(state.resultado)


# st_folium(mapa,feature_group_to_add=fg)
