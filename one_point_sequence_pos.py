#################################################################################################################
# Autores: Equipo Knight Flight Technologies
# Fecha de creación: Semana 3
# Fecha de última modificación: Semana 4
# Descripción: Código para mandar el dron a una coordenada (x,y) y mantenerse a una altura de 1 metro 
# Formato de nombrar variables y funciones: Minúsculas y descriptivas
# Comentado por: Adrian Lara Guzman

#Código basado en https://github.com/bitcraze/crazyflie-lib-python/blob/master/examples/positioning/initial_position.py
#  Copyright (C) 2019 Bitcraze AB

#################################################################################################################


import math
import time

import cflib.crtp
from cflib.crazyflie import Crazyflie
from cflib.crazyflie.log import LogConfig
from cflib.crazyflie.syncCrazyflie import SyncCrazyflie
from cflib.crazyflie.syncLogger import SyncLogger
from cflib.utils import uri_helper

# URI to the Crazyflie to connect to
uri = uri_helper.uri_from_env(default='radio://0/80/2M/E7E7E7E701')

# Change the sequence according to your setup
#             x    y    z
sequence = [
    (0, 0, 1), #Centro
    (0.3, -0.3, 1) #cooredenaa del punto
    
]

##################################Funcion para implementar el filtro de kalman##########################################################
def wait_for_position_estimator(scf):
    print('Waiting for estimator to find position...')

    log_config = LogConfig(name='Kalman Variance', period_in_ms=500)
    log_config.add_variable('kalman.varPX', 'float')
    log_config.add_variable('kalman.varPY', 'float')
    log_config.add_variable('kalman.varPZ', 'float')

    var_y_history = [1000] * 10
    var_x_history = [1000] * 10
    var_z_history = [1000] * 10

    threshold = 0.001

    with SyncLogger(scf, log_config) as logger:
        for log_entry in logger:
            data = log_entry[1]

            var_x_history.append(data['kalman.varPX'])
            var_x_history.pop(0)
            var_y_history.append(data['kalman.varPY'])
            var_y_history.pop(0)
            var_z_history.append(data['kalman.varPZ'])
            var_z_history.pop(0)

            min_x = min(var_x_history)
            max_x = max(var_x_history)
            min_y = min(var_y_history)
            max_y = max(var_y_history)
            min_z = min(var_z_history)
            max_z = max(var_z_history)

            # print("{} {} {}".
            #       format(max_x - min_x, max_y - min_y, max_z - min_z))

            if (max_x - min_x) < threshold and (
                    max_y - min_y) < threshold and (
                    max_z - min_z) < threshold:
                break

###############Funcion que recibe las posiciones iniciales del dron  y utiliza el filtro del Kalman#######################################################################
def set_initial_position(scf, x, y, z, yaw_deg):
    scf.cf.param.set_value('kalman.initialX', x)
    scf.cf.param.set_value('kalman.initialY', y)
    scf.cf.param.set_value('kalman.initialZ', z)

    yaw_radians = math.radians(yaw_deg)
    scf.cf.param.set_value('kalman.initialYaw', yaw_radians)

###################Funcion que se reinicia los valores anteriores almacenados en el filtro de kalman#######################################
def reset_estimator(scf):
    cf = scf.cf
    cf.param.set_value('kalman.resetEstimation', '1')
    time.sleep(0.1)
    cf.param.set_value('kalman.resetEstimation', '0')

    #se llama a la siguiente funcion
    wait_for_position_estimator(cf)

#################Funcion que manda llamar la sequencia de puntos que debe seguir el dron##################################################
def run_sequence(scf, sequence, base_x, base_y, base_z, yaw):
    cf = scf.cf

    for position in sequence:
        print('Setting position {}'.format(position))

        x = position[0] + base_x
        y = position[1] + base_y
        z = position[2] + base_z

        for i in range(50):
            cf.commander.send_position_setpoint(x, y, z, yaw)
            time.sleep(0.1)

    cf.commander.send_stop_setpoint()
    # Make sure that the last packet leaves before the link is closed
    # since the message queue is not flushed before closing
    time.sleep(0.1)


if __name__ == '__main__':
    cflib.crtp.init_drivers()

    # Set these to the position and yaw based on how your Crazyflie is placed
    # on the floor
    initial_x = 2.4
    initial_y = 3.15
    initial_z = 0.0
    initial_yaw = 90  # In degrees
    # 0: positive X direction
    # 90: positive Y direction
    # 180: negative X direction
    # 270: negative Y direction

    #####################conexion al dron####################################################
    with SyncCrazyflie(uri, cf=Crazyflie(rw_cache='./cache')) as scf:

        set_initial_position(scf, initial_x, initial_y, initial_z, initial_yaw)
        reset_estimator(scf)
        run_sequence(scf, sequence,
                     initial_x, initial_y, initial_z, initial_yaw)
        
       