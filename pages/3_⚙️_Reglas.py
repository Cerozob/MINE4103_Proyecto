import streamlit as st
from streamlit import session_state as state
from pages.utils import rules
from code_editor import code_editor
import json

rules.load_all()


def dumps_wrapper(obj):
    return json.dumps(obj, indent=4)


def save_json_from_code(code_editor_object):
    save_action = code_editor_object['type']
    code = code_editor_object["text"].strip()
    if save_action == "submit" and len(code) > 0:
        print("updated json from: ",code_editor_object)
        if state.órdenes is not None and "cluster" in state.órdenes:
            del state.órdenes["cluster"]
            print("deleted clusters for recalculation")
        return json.loads(code)
    return None


custombuttons = [{
    "name": "Guardar",
    "feather": "Save",
    "alwaysOn": True,
    #   "hasText": True,
    "commands": ["submit"],
    "style": {"bottom": "0.46rem", "right": "0.4rem"}
}]


st.set_page_config("Reglas del sistema", page_icon="⚙️")
st.title("Reglas del sistema")
st.write("Aquí encontrarás las reglas que componen el sistema.")
st.write("Puedes modificarlas para cambiar el comportamiento del sistema.")

# Display the rules
st.write("## Capacidades de los vehículos")
st.write("Aquí puedes modificar las capacidades de los vehículos.")
capacities_code = code_editor(dumps_wrapper(
    state.capacities), lang="json", buttons=custombuttons)
new_capacities = save_json_from_code(capacities_code)
if new_capacities is not None:
    state.capacities = new_capacities
    st.toast("Capacidades guardadas.")
if st.button("Restaurar capacidades"):
    state.capacities = rules.load_capacities()
    st.toast("Capacidades restauradas.")

st.write("## Reglas de cajas")
st.write("Aquí puedes modificar las reglas para las cajas necesarios.")
box_rules_code = code_editor(dumps_wrapper(
    state.box_rules), lang="json", buttons=custombuttons)
new_box_rules = save_json_from_code(box_rules_code)
if new_box_rules is not None:
    state.box_rules = new_box_rules
    st.toast("Reglas de cajas guardadas.")
if st.button("Restaurar reglas de cajas"):
    state.box_rules = rules.load_box_rules()
    st.toast("Reglas de cajas restauradas.")

st.write("## Reglas de vehículos")
st.write("Aquí puedes modificar las reglas para los vehículos necesarios.")
truck_rules_code = code_editor(dumps_wrapper(
    state.truck_rules), lang="json", buttons=custombuttons)
save_truck_rules = st.button("Guardar reglas de vehículos")
new_truck_rules = save_json_from_code(truck_rules_code)
if new_truck_rules is not None:
    state.truck_rules = new_truck_rules
    st.toast("Reglas de vehículos guardadas.")
if st.button("Restaurar reglas de vehículos"):
    state.truck_rules = rules.load_truck_rules()
    st.toast("Reglas de vehículos restauradas.")

st.write("## Reglas de costos de envíos")
st.write("Aquí puedes modificar las reglas para los costos de envío.")
costo_envio_rules_code = code_editor(dumps_wrapper(
    state.costo_envio_rules), lang="json", buttons=custombuttons)
new_costo_envio_rules = save_json_from_code(costo_envio_rules_code)
if new_costo_envio_rules is not None:
    state.costo_envio_rules = new_costo_envio_rules
    st.toast("Reglas de costo de envío guardadas.")
if st.button("Restaurar reglas de costo de envío"):
    state.costo_envio_rules = rules.load_costo_envio_rules()
    st.toast("Reglas de costo de envío restauradas.")

if st.button("**Restaurar todas las reglas**", use_container_width=True, type="primary"):
    state.capacities = rules.load_capacities()
    state.box_rules = rules.load_box_rules()
    state.truck_rules = rules.load_truck_rules()
    state.costo_envio_rules = rules.load_costo_envio_rules()
    st.toast("Todas las reglas restauradas.")
    st.rerun()
