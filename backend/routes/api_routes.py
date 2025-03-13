# routes/api_routes.py
from flask import Blueprint, jsonify, request
from backend.services.heartbeat_service import heartbeat_service
from backend.services.serial_service import send_topology_data, setComPort

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
    return setComPort(port_name)


@api_test.route('/set/topology', methods=['POST'])
def set_topology():
    data = request.json
    return send_topology_data(data['value'])
