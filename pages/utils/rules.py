from business_rules.engine import run_all
from business_rules.variables import BaseVariables, numeric_rule_variable,boolean_rule_variable
from business_rules.actions import BaseActions, rule_action
from streamlit import session_state as state
from pathlib import Path
import json
import math


def load_capacities():
    capacities_path = Path("./assets/capacities.json")
    with open(capacities_path, "rt") as f:
        state.capacities = json.load(f)
    return state.capacities


def load_box_rules():
    box_rules_path = Path("./assets/box_rules.json")
    with open(box_rules_path, "rt") as f:
        state.box_rules = json.load(f)
    return state.box_rules


def load_truck_rules():
    truck_rules_path = Path("./assets/truck_rules.json")
    with open(truck_rules_path, "rt") as f:
        state.truck_rules = json.load(f)
    return state.truck_rules


def load_costo_envio_rules():
    costo_envio_rules_path = Path("./assets/costo_envio_rules.json")
    with open(costo_envio_rules_path, "rt") as f:
        state.costo_envio_rules = json.load(f)
    return state.costo_envio_rules


def load_all():

    if "box_rules" not in state:
        load_box_rules()

    if "truck_rules" not in state:
        load_truck_rules()

    if "costo_envio_rules" not in state:
        load_costo_envio_rules()

    if "capacities" not in state:
        load_capacities()


load_all()


def run_rules_boxes(products, num_boxes=None, num_products_out=None,is_sueros=False):

    user = {"products": products, "num_boxes": num_boxes,
        "num_products_out": num_products_out, "is_sueros": is_sueros}

    # Define Variables class
    class UserVariables(BaseVariables):
        def __init__(self, user):
            self.user = user

        @numeric_rule_variable(label="Number of products")
        def products(self):
            return self.user['products']

        @numeric_rule_variable(label="Number of boxes")
        def num_boxes(self):
          return self.user['num_boxes']
        
        
        @boolean_rule_variable(label="Is sueros")
        def is_sueros(self):
            return self.user['is_sueros']
        

    # Define Actions class
    class UserActions(BaseActions):
        def __init__(self, user):
            self.user = user

        @rule_action(label="Calcular cajas para Sueros")
        def set_num_boxes_sueros(self):
            self.user['num_boxes'] = self.user['products']//6

        @rule_action(label="Calcular sueros individuales")
        def set_num_products_out(self):
            self.user['num_products_out'] = self.user['products'] % 6

        @rule_action(label="Cajas para productos")
        def set_num_boxes(self):
          self.user['num_boxes'] = math.ceil(self.user['products']/36000)

    # Define rules in JSON format
    rules = state.box_rules

    # Execute rules
    run_all(
        rule_list=rules,
        defined_variables=UserVariables(user),
        defined_actions=UserActions(user),
        stop_on_first_trigger=True
    )

    return user


def run_rules_truck(containers, num_trucks=None,num_bikes=None):

    user = {"containers": containers, "num_trucks": num_trucks, "num_bikes": num_bikes}

    # Define Variables class
    class UserVariables(BaseVariables):

        def __init__(self, user):
            self.user = user

        @numeric_rule_variable(label="Number of containers")
        def containers(self):
            return self.user['containers']

    # Define Actions class
    class UserActions(BaseActions):
        def __init__(self, user):
            self.user = user

        @rule_action(label="Calcular camiones")
        def set_containers_over_truck(self):
            num_bikes = 0
            num_trucks = self.user['containers']//state.capacities['truck']
            self.user['containers'] = self.user['containers'] - \
                (num_trucks*state.capacities['truck'])
            if self.user['containers'] > 20:
                num_trucks += 1
                self.user['containers'] = 0
            else:
                num_bikes = self.user['containers']//state.capacities['bike']
                self.user['containers'] = 0

            self.user['num_trucks'] = num_trucks
            self.user['num_bikes'] = num_bikes
            if num_trucks == 0 and num_bikes == 0:
                self.user['num_bikes'] = 1

        @rule_action(label="Calcular otros")
        def set_containers_under_truck(self):
            num_trucks = 0
            num_bikes = 0
            if self.user['containers'] > 20:
                num_trucks += 1
                self.user['containers'] = 0
            else:
                num_bikes = self.user['containers']//state.capacities['bike']
                self.user['containers'] = 0
            # avoid having both bikes and trucks as 0
            self.user['num_trucks'] = num_trucks
            self.user['num_bikes'] = num_bikes
            if num_trucks == 0 and num_bikes == 0:
                self.user['num_bikes'] = 1

    rules = state.truck_rules
    # ! hay que asignar las capacidades de los vehículos manualmente, esto es porque no se pueden pasar variables de python a las reglas en JSON
    for idx,rul in enumerate(rules):
        conditions_all = rul['conditions']['all'] if 'all' in rul['conditions'] else []
        conditions_any = rul['conditions']['any'] if 'any' in rul['conditions'] else []
        for idx2,cond in enumerate(conditions_all):
            current_value = cond['value']
            if current_value in state.capacities:
                rules[idx]['conditions']['all'][idx2]['value'] = state.capacities[current_value]
        for idx2,cond in enumerate(conditions_any):
            current_value = cond['value']
            if current_value in state.capacities:
                rules[idx]['conditions']['any'][idx2]['value'] = state.capacities[current_value]

    # Execute rules
    run_all(
        rule_list=rules,
        defined_variables=UserVariables(user),
        defined_actions=UserActions(user),
        stop_on_first_trigger=True
    )
    return user


def run_rules_delivery_cost(distance,num_trucks,num_bikes,total_value=0):

    user = {"distance": distance, "num_trucks": num_trucks, "num_bikes": num_bikes, "total_value": total_value}
    # Define Variables class
    class UserVariables(BaseVariables):
        def __init__(self, user):
            self.user = user

        @numeric_rule_variable(label="total value of delivery")
        def total_value(self):
            return self.user['total_value']

        @numeric_rule_variable(label="number of trucks")
        def num_trucks(self):
            return self.user['num_trucks']

        @numeric_rule_variable(label="number of bikes")
        def num_bikes(self):
            return self.user['num_bikes']

    # Define Actions class
    class UserActions(BaseActions):
        def __init__(self, user):
            self.user = user

        @rule_action(label="Calcular costo de envío")
        def set_total_value(self):

            value_truck = self.user['num_trucks'] * \
                (10000 + (3000*self.user['distance']))  # peso/km
            value_bike = self.user['num_bikes'] * \
                (2000 + (500*self.user['distance']))

            self.user['total_value'] = value_truck + value_bike

    # Define rules in JSON format
    rules = [
        {
            "conditions": {
                "any": [
                    {
                        "name": "num_trucks",
                        "operator": "greater_than_or_equal_to",
                        "value": 0
                    },
                    {
                        "name": "num_bikes",
                        "operator": "greater_than_or_equal_to",
                        "value": 0
                    }
                ]
            },
            "actions": [
                {
                    "name": "set_total_value"
                }
            ]
        },
        {
            "conditions": {
                "all": [
                    {
                        "name": "distance",
                        "operator": "greater_than_or_equal_to",
                        "value": 0
                    }
                ]
            },
            "actions": [
                {
                    "name": "set_total_value"
                }
            ]
        }
    ]

    # Execute rules
    run_all(
        rule_list=rules,
        defined_variables=UserVariables(user),
        defined_actions=UserActions(user),
        stop_on_first_trigger=True
    )
    return user


# user = {"products": 305, "num_boxes": None, "num_products_out": None}

# user2 = {"containers": 200, "num_trucks": None, "num_bikes": None}

# user3 = {"distance": 10, "num_trucks": 2, "num_bikes": 3, "total_value": 0}

# result1 = run_rules_boxes(user)
# result2 = run_rules_truck(user2)
# result3 = run_rules_delivery_cost(user3)
