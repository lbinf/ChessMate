from app.engine import engine_instance

def get_params():
    return engine_instance.params

def set_param(name, value):
    engine_instance.params[name] = value
    engine_instance.save_parameters()
    return engine_instance.params 