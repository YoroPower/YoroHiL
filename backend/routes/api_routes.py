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
    return jsonify({"status": "OK","value": heartbeat_service.value})


@api_bp.route('/device', methods=['POST'])
def set_device():
    data = request.json
    heartbeat_service.value = data.get('value', heartbeat_service.value)
    return jsonify({"status": "OK","value": heartbeat_service.value})


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

@api_bp.route('/sim/pinio', methods=['POST'])
def set_sim_pinio():
    data = request.get_json()
    if not data or 'output_pins' not in data or not isinstance(data['output_pins'], list):
        return jsonify({
            'status': 'error',
            'message': 'Invalid request body: output_pins must be a list'
        }), 400

    I_pins = []
    for pin in data['input_pins']:
        # 验证字段
        if not isinstance(pin.get('branch_name'), str):
            return jsonify({
                'status': 'error',
                'message': 'Invalid branch_name: must be an str'
            }), 400
        if pin.get('pin_name') not in obj_SimMatrix.INID_PINS:
            return jsonify({
                'status': 'error',
                'message': f"Invalid pin_name: {pin.get('pin_name')} is not a valid pin"
            }), 400

        I_pins.append({
            'branch_name': pin['branch_name'],
            'pin_name': pin['pin_name']
        })

    if not data or 'output_pins' not in data or not isinstance(data['output_pins'], list):
        return jsonify({
            'status': 'error',
            'message': 'Invalid request body: output_pins must be a list'
        }), 400

    O_pins = []
    for pin in data['output_pins']:
        # 验证字段
        if not isinstance(pin.get('branch_name'), str):
            return jsonify({
                'status': 'error',
                'message': 'Invalid branch_name: must be an str'
            }), 400
        if not isinstance(pin.get('type'), str):
            return jsonify({
                'status': 'error',
                'message': 'Invalid type: must be an str'
            }), 400
        if pin.get('pin_name') not in obj_SimMatrix.OUTID_PINS:
            return jsonify({
                'status': 'error',
                'message': f"Invalid pin_name: {pin.get('pin_name')} is not a valid pin"
            }), 400

        O_pins.append({
            'branch_name': pin['branch_name'],
            'pin_name': pin['pin_name'],
            'type': pin['type']
        })

    return obj_SimMatrix.pinIOConfig(I_pins, O_pins)


@api_bp.route('/sim/range', methods=['POST'])
def set_sim_range():
    data = request.get_json()
    for data_entry in data:
        if data_entry.get('pin_name') not in obj_SimMatrix.OUTID_PINS:
            return jsonify({
                'status': 'error',
                'message': f"Invalid pin_name: {data_entry.get('pin_name')} is not a valid pin"
            }), 400
    return obj_SimMatrix.rangeConfig(data)

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


