ocpp_client_instance = None

def set_ocpp_client_instance(instance):
    global ocpp_client_instance
    ocpp_client_instance = instance

def get_ocpp_client():
    return ocpp_client_instance
