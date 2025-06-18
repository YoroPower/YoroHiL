# routes/api_routes.py
from flask import Blueprint, jsonify, request
from backend.services.heartbeat_service import heartbeat_service
from backend.services.serial_service import  setComPort
from backend.cirSim.simMatrix import obj_SimMatrix
from backend.cirSim.hardMatrix import obj_HardMatrix
from backend.clients.freeMaster_client import freeMaster_client

api_bp = Blueprint('api', __name__)
api_test = Blueprint('test', __name__)


@api_bp.route('/device', methods=['GET'])
def get_device():
    return jsonify({"value": heartbeat_service.value})


@api_bp.route('/device', methods=['POST'])
def set_device():
    data = request.json
    heartbeat_service.value = data.get('value', heartbeat_service.value)
    return jsonify({"value": heartbeat_service.value})


@api_bp.route('/compots', methods=['GET'])
def get_compots():
    import serial.tools.list_ports
    ports = [{"name": port.device, "description": port.description}
             for port in serial.tools.list_ports.comports()]
    return jsonify(ports)


@api_bp.route('/compots', methods=['POST'])
def set_compots():
    data = request.json
    port_name = data.get('port')
    # return setComPort(port_name)
    return obj_HardMatrix.connectCfg(port_name)

@api_bp.route('/sim/xml', methods=['POST'])
def set_sim_XML():
    data = request.json
    xml_path = data.get('path')
    return obj_SimMatrix.loadXML(xml_path)


@api_bp.route('/sim/net', methods=['POST'])
def set_sim_NET():
    data = request.json
    net_path = data.get('path')
    return obj_SimMatrix.loadNET(net_path)


@api_bp.route('/sim/open', methods=['POST'])
def set_sim_open():
    data = request.json
    return obj_SimMatrix.simOpen()


@api_bp.route('/sim/stop', methods=['POST'])
def set_sim_stop():
    data = request.json
    return obj_HardMatrix.NewCtrlSimStop()


@api_bp.route('/hw/connect', methods=['POST'])
def set_hw_connect():
    data = request.json
    return obj_HardMatrix.connect()


@api_test.route('/set/topology', methods=['POST'])
def test_set_topology():
    return jsonify({"status": "OK"})


@api_test.route('/ReadVariable', methods=['POST'])
def test_ReadVariable():
    data = request.json
    name = data.get('name')
    try:
        v = freeMaster_client.read_variable(name)
    except Exception as e:
        return jsonify({"status": "ERR", "reason": str(e)})

    return jsonify({"status": "OK","value": v})


