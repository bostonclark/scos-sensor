from capabilities.models import SensorDefinition, Antenna, Preselector, Receiver

def test_sensor_def():
    ant = Antenna()
    ps = Preselector()
    rx = Receiver()
    str(SensorDefinition(host_controller="test_controller", antenna=ant, preselector=ps, receiver=rx))
