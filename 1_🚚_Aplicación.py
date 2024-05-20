import streamlit as st
import st_on_hover_tabs as hovertabs
from pathlib import Path
import pandas as pd
st.set_page_config(page_title="Página principal", page_icon="🏠")

pedidos_df = pd.DataFrame({"Producto": ["Paracetamol", "Ibuprofeno", "Omeprazol"],
                           "Cantidad": [100, 200, 300],
                           "Esto es un ejemplo": ["Hola", "Mundo", "Python"]
                           })

farmulogo_path = Path("./assets/farmu_logo.svg")
farmudots_path = Path("./assets/farmu_dots.svg")


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
    modificado_df = st.data_editor(pedidos_df,num_rows="dynamic")
    st.write(f"se han ingresado {modificado_df.shape[0]} pedidos")
    st.write("Una vez que hayas ingresado tus pedidos, presiona el botón de abajo para estimar los envíos")
    if st.button("Estimar envíos"):
        resultado = procesar_pedidos(modificado_df)
        st.write(resultado)
    
