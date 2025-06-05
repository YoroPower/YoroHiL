import websockets
import jsonrpcclient
import asyncio
import logging

class FreeMasterClient:
    def __init__(
            self,
            machine_url='127.0.0.1',
            service_port='8090',
            conn_type='RS232',
            port='COM4',
            speed='115200',
            **kwargs
    ):
        self.machine_url = machine_url
        self.service_port = service_port
        self.conn_type = conn_type
        self.port = port
        self.speed = speed
        self.extra_conn_args = kwargs  # 支持更多参数
        self.service_protocol = 'ws://'
        self.service_url = f"{self.service_protocol}{self.machine_url}:{self.service_port}"
        self.ws = None
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        self.pp_R_base = None
        self.MATRIX_MAX_SIZE = None
        self.COMB_MAX_NUM = None
        self.pp_LC_base = None

    def _build_connection(self):
        # 基本参数
        conn = f"{self.conn_type}; port={self.port};speed={self.speed};"
        # 额外参数
        for k, v in self.extra_conn_args.items():
            conn += f"{k}={v};"
        return conn

    async def _connect(self):
        if self.ws is None or self.ws.close:
            self.ws = await websockets.connect(self.service_url)

    async def _send_request(self, method, *args):
        await self._connect()
        await self.ws.send(jsonrpcclient.request_json(method, args))
        response = jsonrpcclient.parse_json(await self.ws.recv())
        if isinstance(response, jsonrpcclient.Ok):
            if response.result['success']:
                return response.result['data']
            else:
                raise Exception(response.result['error'])
        else:
            raise Exception(response.message)

    def init(self):
        async def _init():
            try:
                await self._connect()
                connection = self._build_connection()
                await self._send_request('StartComm', connection)
                data = await self._send_request('ReadTSA')
                data_base = await self._send_request('GetSymbolInfo', "SysMatrixRun.pp_R[0][0][0]")
                data = await self._send_request('GetSymbolInfo', "SysMatrixRun.pp_R[0][1][0]")
                self.pp_R_base = data_base['addr']
                self.MATRIX_MAX_SIZE = int((data['addr'] - data_base['addr']) / 4)
                data_base = await self._send_request('GetSymbolInfo', "SysMatrixRun.pp_LC[0][0]")
                self.pp_LC_base = data_base['addr']
                self.COMB_MAX_NUM = int((self.pp_LC_base - self.pp_R_base) / (self.MATRIX_MAX_SIZE * self.MATRIX_MAX_SIZE * 4))

                # 注册pp_R
                for i in range(self.COMB_MAX_NUM):
                    for j in range(self.MATRIX_MAX_SIZE):
                        for k in range(self.MATRIX_MAX_SIZE):
                            addr = self.pp_R_base + ((i * self.MATRIX_MAX_SIZE * self.MATRIX_MAX_SIZE + j * self.MATRIX_MAX_SIZE + k) * 4)
                            variable = {
                                'name': f"SysMatrixRun.pp_R[{i}][{j}][{k}]",
                                'addr': addr,
                                'type': 'float',
                                'size': 4
                            }
                            try:
                                await self._send_request('DefineVariable', variable)
                            except Exception as e:
                                logging.warning(f"DefineVariable failed: {variable['name']} - {e}")

                # 注册pp_LC
                for i in range(self.MATRIX_MAX_SIZE):
                    for j in range(self.MATRIX_MAX_SIZE):
                        addr = self.pp_LC_base + ((i * self.MATRIX_MAX_SIZE + j) * 4)
                        variable = {
                            'name': f"SysMatrixRun.pp_LC[{i}][{j}]",
                            'addr': addr,
                            'type': 'float',
                            'size': 4
                        }
                        try:
                            await self._send_request('DefineVariable', variable)
                        except Exception as e:
                            logging.warning(f"DefineVariable failed: {variable['name']} - {e}")

                # 注册一维数组
                one_dim_float = ['YL', 'YC', 'YR', 'vhs', 'J']
                for arr in one_dim_float:
                    for i in range(self.MATRIX_MAX_SIZE):
                        variable = {
                            'name': f"SysMatrixRun.{arr}[{i}]",
                            'addr': f"SysMatrixRun.{arr}[{i}]",
                            'type': 'float',
                            'size': 4
                        }
                        try:
                            await self._send_request('DefineVariable', variable)
                        except Exception as e:
                            logging.warning(f"DefineVariable failed: {variable['name']} - {e}")

                # 注册attr
                for i in range(self.MATRIX_MAX_SIZE):
                    variable = {
                        'name': f"SysMatrixRun.attr[{i}]",
                        'addr': f"SysMatrixRun.attr[{i}]",
                        'type': 'uint',
                        'size': 1
                    }
                    try:
                        await self._send_request('DefineVariable', variable)
                    except Exception as e:
                        logging.warning(f"DefineVariable failed: {variable['name']} - {e}")

                await self._send_request('StopComm')
                return True
            except Exception as e:
                logging.error(f"Init failed: {e}")
                return False

        return self.loop.run_until_complete(_init())

    def start(self):
        try:
            self.loop.run_until_complete(self._send_request('StartComm', self.connection))
            return True
        except Exception as e:
            logging.error(f"Start failed: {e}")
            return False

    def stop(self):
        try:
            self.loop.run_until_complete(self._send_request('StopComm'))
            return True
        except Exception as e:
            logging.error(f"Stop failed: {e}")
            return False

    def write_variable(self, name, value):
        try:
            self.loop.run_until_complete(self._send_request('WriteVariable', name, value))
            return True
        except Exception as e:
            logging.error(f"WriteVariable failed: {name} - {e}")
            return False

    def read_variable(self, name):
        try:
            return self.loop.run_until_complete(self._send_request('ReadVariable', name))
        except Exception as e:
            logging.error(f"ReadVariable failed: {name} - {e}")
            return None


freeMaster_client = FreeMasterClient()

if __name__ == "__main__":
    client = FreeMasterClient()
    client.init()
    client.start()
    client.write_variable('SysMatrixRun.vhs[5]', 123456)
    value = client.read_variable('SysMatrixRun.vhs[5]')
    print('Read value:', value)
    client.stop()