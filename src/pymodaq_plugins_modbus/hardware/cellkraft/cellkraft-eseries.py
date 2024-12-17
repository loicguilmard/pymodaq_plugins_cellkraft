from pymodaq.utils.logger import set_logger, get_module_name
logger = set_logger(get_module_name(__file__))

from pymodaq_plugins_modbus.hardware.tcpmodbus import SyncModBusInstrument

    # WRITE
    #
    # pump control : register 9107 value [0 auto 1 manual 2 prime] default 1
    # SP temp var °C : register 9300 value [] default 10
    # RH% : register 9240 default 10
    # SP flow(g/min) register 9310 default 10
    # SP TEMP tube °C register 9355
    #
    # READ
    #
    # steam temp 4148
    # Air humidity 4628
    # flow (g/min) 6518
    # pressure(bar) 5268
    # Tube temp 4468
    # pump % 6158
    #
    # turn down => write 0 to register 9310
    # read status 6518

Eseries_Config= {
        "general": {
            "scaling_default": 1,
            },
        "Pump": {
            "reference": "Pump",
            "write_address": 9107,
            "authorized_writevalue": [0, 1, 2],
            "default_writevalue": 0,
            },
        "Steam" : {
            "reference": "Steam",
            "type": int,
            "unit": "C",
            "read_address": 4148,
            "readscaling": 10,
            "write_address": 9300,
            "authorized_writevalue": range(0,200,1),
            "default_writevalue": 0
            },
        "Air": {
            "reference": "RH",
            "unit": "%",
            "type": int,
            "read_address": 4628,
            "write_address": 9240,
            "authorized_writevalue": range(0, 105, 1),
            "default_writevalue": 105,
            "scaling": 10
            },
        "Flow": {
            "reference": "Flow",
            "unit": "g/min",
            "type": int,
            "read_address": 6518,
            "write_address": 9310,
            "authorized_writevalue": range(0, 25, 0.1),
            "default_writevalue": 105,
            "scaling": 10
            },
        "Tube": {
            "reference": "Tube",
            "unit": "C",
            "type": int,
            "read_address": 4468,
            "readscaling": 10,
            "write_address": 9355,
            "authorized_writevalue": range(0, 200, 1),
            "default_writevalue": 105
            },
        "Pressure": {
            "reference": "Pressure",
            "unit": "Bar",
            "type": int,
            "read_address": 5268,
            "readscaling": 100
            #"write_address": 9355,
            #"authorized_writevalue": range(0, 200, 1),
            #"default_writevalue": 105
            },
        }

def registerfactory(reference, mode):
    """This will create all the function from dict[ref]

    :param reference: the name of the item
    :return:
    """
    def decorator(function):
        def wrapped(*args):
            function(*args)
        return wrapped
    return decorator


class CellKraftE1500Drivers:
    """TCP ModBus driver for the Steam Generator CellKraft E-series

    Relies on a custom tcpmodules based on pymodbus (source : https://github.com/pymodbus-dev/pymodbus
    documentation : https://pymodbus.readthedocs.io/en/latest/)
    """
    def __init__(self, host):
        """Initialize the Steam Generator driver

        :param host: hostname or ip adress
        """
        self.instr = SyncModBusInstrument(host)
        self.host = host
        self.registers = {}
        self.init = False

    def init_hardware(self):
        """Connect and initialize the Steam Generator

        """
        self.init = self.instr.ini_hw()

    def stop(self):
        """Stop procedure

        :return:
        """
        self.SP_Flow(0)

    @registerfactory("pump", "write")
    def PumpSetMode(self, value: str = "auto"):
        """Writing the pump mode

        :param value: human-readable equivalent of the 3 allowed values (0 auto, 1 manual, 2 prime) defaulting to auto
        """
        if not self.registers["PumpSetMode"]:
            self.registers["PumpSetMode"] = {
                "register": Eseries_Config["Pump"]["write_address"],
                "mode": "write"
            }
        order: int
        match value:
            case "auto":
                order = 0
            case "manual":
                order = 1
            case "prime":
                order = 2
            case _:
                order = 0
        try:
            self.instr.write(self.registers["PumpSetMode"]["register"],
                             order)
        except Exception as e:
            raise (Exception, f"error in {self.__qualname__}")

    @registerfactory("steam", "write")
    def SP_SteamT(self, temperature: int=10):
        """Set the SP Steam temperature in °C

        :param value: int °C
        """
        if not self.registers["SP_SteamT"]:
            self.registers["SP_SteamT"] = {
                "register": Eseries_Config["Steam"]["write_address"],
                "mode": "write"
            }
        if isinstance(temperature, int):
            try:

                self.instr.write(self.registers["SP_SteamT"]["register"],
                                 temperature)
            except Exception as e:
                raise Exception
        else:
            raise (TypeError, f"type(temperature) passed to {self.__qualname__}.SP_vapT must be an int") # add {self.__class__.__name__}. ?

    @registerfactory("air", "write")
    def RH(self, relativehumidity: int=105):
        """Set the relative humidity in %

        :param relativehumidity: int% relative humdity
        """
        if not self.registers["RH"]:
            self.registers["RH"] = {
                "register": Eseries_Config["Air"]["write_address"],
                "mode": "write",
                "scaling": Eseries_Config["Air"]["scaling"]
            }
        if isinstance(relativehumidity, int):
            try:
                self.instr.write(self.registers["RH"]["register"],
                                 relativehumidity*self.registers["RH"]["scaling"])
            except Exception as e:
                raise Exception
        else:
            raise (TypeError, f"type(relativehumidity) passed to {self.__qualname__}.RH() must but int")

    @registerfactory("flow", "write")
    def SP_Flow(self, flow: int):
        """Set the flow in g/min

        :param flow:
        """
        if not self.registers["SP_Flow"]:
            self.registers["SP_Flow"] = {
                "register": Eseries_Config["Flow"]["write_address"],
                "mode": "write",
                "scaling": Eseries_Config["Flow"]["scaling"]
            }
        if isinstance(flow, int):
            try:

                self.instr.write(self.registers["SP_Flow"]["register"],
                                 flow*self.registers["SP_Flow"]["scaling"])
            except Exception as e:
                raise Exception
        else:
            raise (TypeError, f"type(flow) passed to {self.__qualname__}.SP_Flow() must but int")

    @registerfactory("tube", "write")
    def SP_Tube_Temp(self, temperature: int):
        """Set the tube temperature

        :param int: tube temperature setpoint
        :return:
        """
        if not self.registers["SP_Tube_Temp"]:
            self.registers["SP_Tube_Temp"] = {
                "register": Eseries_Config["Tube"]["write_address"],
                "mode": "write"
            }
        if isinstance(temperature, int):
            try:

                self.instr.write(self.registers["SP_Tube_Temp"]["register"],
                                 temperature)
            except Exception as e:
                raise Exception
        else:
            raise (TypeError, f"type(temperature) passed to {self.__qualname__}.SP_Tube_Temp() must but int")

    @registerfactory("steam", "read")
    def Get_Steam_T(self):
        """Get the steam temperature

        :return: temperature int °C
        """
        if not self.registers["Get_Steam_T"]:
            self.registers["Get_Steam_T"] = {
                "register": Eseries_Config["Steam"]["read_address"],
                "mode": "read",
                "scaling": Eseries_Config["Steam"]["readscaling"]
            }
        ReadResult = self.instr.read(self.registers["Get_Steam_T"]["register"])
        if isinstance(Exception, ReadResult):
            raise ReadResult
        else:
            return ReadResult.registers[0]/self.registers["Get_Steam_T"]["readscaling"]

    @registerfactory("air", "read")
    def Get_Air_H(self):
        """Get the air humidity

        :return: int %
        """
        if not self.registers["Get_Air_H"]:
            self.registers["Get_Air_H"] = {
                "register": Eseries_Config["Air"]["read_address"],
                "mode": "read",
                "scaling": Eseries_Config["Air"]["scaling"]
            }
        ReadResult = self.instr.read(self.registers["Get_Air_H"]["register"])
        if isinstance(Exception, ReadResult):
            raise ReadResult
        else:
            return ReadResult.registers[0]/self.registers["Get_Air_H"]["scaling"]

    @registerfactory("steam", "read")
    def Get_Flow(self):
        """Get the air humidity

        :return: int %
        """
        if not self.registers["Get_Flow"]:
            self.registers["Get_Flow"] = {
                "register": Eseries_Config["Flow"]["read_address"],
                "mode": "read",
                "scaling": Eseries_Config["Flow"]["scaling"]
            }
        ReadResult = self.instr.read(self.registers["Get_Flow"]["register"])
        if isinstance(Exception, ReadResult):
            raise ReadResult
        else:
            return ReadResult.registers[0]/self.registers["Get_Flow"]["scaling"]

    @registerfactory("pressure", "read")
    def Get_Pressure(self):
        """Get the pressure

        :return: int Bar
        """
        if not self.registers["Get_Pressure"]:
            self.registers["Get_Pressure"] = {
                "register": Eseries_Config["Pressure"]["read_address"],
                "mode": "read",
                "scaling": Eseries_Config["Pressure"]["readscaling"]
            }
        ReadResult = self.instr.read(self.registers["Get_Pressure"]["register"])
        if isinstance(Exception, ReadResult):
            raise ReadResult
        else:
            return ReadResult.registers[0]/self.registers["Get_Pressure"]["scaling"]

    @registerfactory("tube", "read")
    def Get_Tube_T(self):
        """Get the tube temperature

        :return: int °C
        """
        if not self.registers["Get_Tube_T"]:
            self.registers["Get_Tube_T"] = {
                "register": Eseries_Config["Tube"]["read_address"],
                "mode": "read",
                "scaling": Eseries_Config["Tube"]["readscaling"]
            }
        ReadResult = self.instr.read(self.registers["Get_Tube_T"]["register"])
        if isinstance(Exception, ReadResult):
            raise ReadResult
        else:
            return ReadResult.registers[0]/self.registers["Get_Tube_T"]["scaling"]
