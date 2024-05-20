import streamlit as st
from streamlit import session_state as state
import st_on_hover_tabs as hovertabs
from pathlib import Path
import pandas as pd
import folium
import json
from streamlit_folium import st_folium
from sklearn.cluster import DBSCAN
from sklearn.preprocessing import StandardScaler
from sklearn.metrics.pairwise import haversine_distances, euclidean_distances

st.set_page_config(page_title="Página principal", page_icon="🏠")


# TODO not use random samples
def randomize(dataframe):
    import random

    bbox_samples ={"lon1":-74.257278,"lat1":4.514137,"lon2":-74.031372,"lat2":4.812523}
    productos_samples = ["Paracetamol", "Ibuprofeno", "Omeprazol"]
    # genrate 100 random samples within the bbox
    dataframe["Producto"] = [random.choice(productos_samples) for _ in range(100)]
    dataframe["Cantidad"] = [random.uniform(1,1000) for _ in range(100)]
    dataframe["lat"] = [random.uniform(bbox_samples["lat1"],bbox_samples["lat2"]) for _ in range(100)] 
    dataframe["lon"] = [random.uniform(bbox_samples["lon1"],bbox_samples["lon2"]) for _ in range(100)]
    return dataframe

if "pedidos" not in state:
    state.pedidos = pd.DataFrame({"Producto": [],
                            "Cantidad": [],
                            "lat": [],
                            "lon": []
                            })
if state.pedidos.empty:
    state.pedidos = randomize(state.pedidos)


farmulogo_path = Path("./assets/farmu_logo.svg")
farmudots_path = Path("./assets/farmu_dots.svg")
bogotamap_path = Path("./assets/bogota_cadastral.json")

with open(bogotamap_path,"rt") as bog:
    bogotamap=json.load(bog)

with open(farmulogo_path, "rt") as logo, open(farmudots_path, "rt") as dots:
    farmulogo = logo.read()
    farmudots = dots.read()


_, col1, _ = st.columns([1, 3, 1])
col1.image(farmudots, use_column_width=True, output_format="SVG")
col1.image(farmulogo, use_column_width=True , output_format="SVG")

st.title("Estimación de envíos para pedidos Farmacéuticos")

def procesar_pedidos(dataframe):
    st.write("Procesando pedidos...")
    # TODO
    with st.spinner("Procesando pedidos..."):
        import time
        time.sleep(2)
        st.write("Pedidos procesados")
    return "TODO: Resultado de la estimación de envíos"

st.write("Sube tu archivo de pedidos para estimar los envíos")
uploaded_file = st.file_uploader("Sube tu archivo de pedidos", type=["csv", "xlsx"])

if uploaded_file is not None:

    st.write(f"Archivo subido: {uploaded_file.name}")
    file_dframe = pd.read_csv(uploaded_file) if uploaded_file.name.endswith(".csv") else pd.read_excel(uploaded_file)
    resultado = procesar_pedidos(file_dframe)
    st.write(resultado)
else:
    st.write("No se ha subido ningún archivo")

    st.write("No sabes en qué formato subir tu archivo?, descarga este ejemplo")
    st.download_button("Descargar ejemplo en csv", "assets/plantilla_pedidos.csv", "plantilla_pedidos.csv", "text/csv")
    st.download_button("Descargar ejemplo en xlsx", "assets/plantilla_pedidos.xlsx", "plantilla_pedidos.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    
    st.write("También puedes ingresar tus pedidos manualmente si lo prefieres")
    modificado_df = st.data_editor(state.pedidos,num_rows="dynamic")
    st.write(f"se han ingresado {modificado_df.shape[0]} pedidos")
    st.write("Una vez que hayas ingresado tus pedidos, presiona el botón de abajo para estimar los envíos")
    if st.button("Estimar envíos"):
        resultado = procesar_pedidos(modificado_df)
        st.write(resultado)

st.write("Información adicional de los pedidos")

st.write("Mapa de ubicaciones de envíos")

mapa = folium.Map(location=[4.6458888888889, -74.0775], zoom_start=11)
fg = folium.FeatureGroup(name="Ubicaciones de envíos")


# for id,pedido in state.pedidos.iterrows():
#     marker = folium.Marker(location=[pedido["lat"], pedido["lon"]],
#                   popup=f"{pedido['Producto']} - {pedido['Cantidad']} unidades",
#                   icon=folium.Icon(color="blue", icon="info-sign"))
#     fg.add_child(marker)

dbscan = DBSCAN(eps=0.25, min_samples=3,metric='haversine')
scaler = StandardScaler()
colorchoices = ['red', 'blue', 'green', 'purple', 'orange', 'darkred','lightred', 'beige', 'darkblue', 'darkgreen', 'cadetblue', 'darkpurple', 'white', 'pink', 'lightblue', 'lightgreen', 'gray', 'black', 'lightgray']
with st.spinner("Estimando clusters de envíos..."):
    state.pedidos[["lat_std", "lon_std"]] = scaler.fit_transform(state.pedidos[["lat", "lon"]])
    state.pedidos["cluster"] = dbscan.fit_predict(state.pedidos[["lat_std", "lon_std"]])
    st.write("Clusters estimados")
    nclusters = state.pedidos["cluster"].nunique()
    print(f"se han estimado {nclusters} clusters de envíos")
    for cluster in state.pedidos["cluster"].unique():
        cluster_df = state.pedidos[state.pedidos["cluster"] == cluster]
        cluster_fg = folium.FeatureGroup(name=f"Cluster {cluster}")
        for idx, pedido in cluster_df.iterrows():
            marker = folium.Marker(location=[pedido["lat"], pedido["lon"]],
                            popup=f"{pedido['Producto']} - {pedido['Cantidad']} unidades. Grupo {cluster}",
                            icon=folium.Icon(color=colorchoices[cluster], icon="info-sign"))
            cluster_fg.add_child(marker)
        mapa.add_child(cluster_fg)  

st_folium(mapa,feature_group_to_add=cluster_fg)
        

# st_folium(mapa,feature_group_to_add=fg)

