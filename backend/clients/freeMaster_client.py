import websockets
import jsonrpcclient
import asyncio


class freeMaster_client:
    def __init__(self, machine_url='127.0.0.1', service_port='8090', connection='RS232; port=COM4;speed=115200;'):
        self.machine_url = machine_url
        self.service_port = service_port
        self.connection = connection
        self.service_protocol = 'ws://'
        self.service_url = f"{self.service_protocol}{self.machine_url}:{self.service_port}"
        self.ws = None
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        self.pp_R_base = None
        self.MATRIX_MAX_SIZE = None
        self.COMB_MAX_NUM = None
        self.pp_LC_base = None

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
            await self._connect()
            await self._send_request('StartComm', self.connection)
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
                        await self._send_request('DefineVariable', variable)

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
                    await self._send_request('DefineVariable', variable)

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
                    await self._send_request('DefineVariable', variable)

            # 注册attr
            for i in range(self.MATRIX_MAX_SIZE):
                variable = {
                    'name': f"SysMatrixRun.attr[{i}]",
                    'addr': f"SysMatrixRun.attr[{i}]",
                    'type': 'uint',
                    'size': 1
                }
                await self._send_request('DefineVariable', variable)

            await self._send_request('StopComm')

        self.loop.run_until_complete(_init())

    def start(self):
        self.loop.run_until_complete(self._send_request('StartComm', self.connection))

    def stop(self):
        self.loop.run_until_complete(self._send_request('StopComm'))

    def write_variable(self, name, value):
        self.loop.run_until_complete(self._send_request('WriteVariable', name, value))

    def read_variable(self, name):
        return self.loop.run_until_complete(self._send_request('ReadVariable', name))


if __name__ == "__main__":
    client = freeMaster_client()
    client.init()
    client.start()
    client.write_variable('SysMatrixRun.vhs[5]', 123456)
    value = client.read_variable('SysMatrixRun.vhs[5]')
    print('Read value:', value)
    client.stop()