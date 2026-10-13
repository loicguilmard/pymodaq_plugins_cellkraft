from pymodaq.utils.data import DataFromPlugins, DataToExport
from pymodaq.control_modules.viewer_utility_classes import DAQ_Viewer_base, comon_parameters, main
from pymodaq.utils.parameter import Parameter
from pymodaq_plugins_cellkraft.hardware.cellkraft.Eseries import CellKraftE1500Drivers

from pymodaq_plugins_cellkraft import config
from pymodaq.utils.logger import set_logger, get_module_name

logger = set_logger(get_module_name(__file__))


class DAQ_0DViewer_Pressure(DAQ_Viewer_base):
    """

        pymodaq Version 5.0.11
        pymodaq-data Version 5.0.23

        Limites thérorique a ne pas dépasser :
            - Flow : 2 g/min                                                                - modifiable     - move
           X- Pressure                                                                      - non modifiable - viewer0D
            - Steam Temperature : 180 °C                                                    - modifiable     - move
            - Tube Temperature : 200 °C                                                     - modifiable     - move
            - RH (Relative Humidity) : 80%                                                  - modifiable     - move

        """

    params = comon_parameters + [
        {
            'title': 'Device:',
            'name': 'device',
            'type': 'str',
            'value': 'Cellkraft E1500 Series',
            'readonly': True
        },
        {
            'title': 'Host:',
            'name': 'host',
            'type': 'str',
            'value': config('Cellkraft', 'DEVICE01', 'host')
        },
        {
            'title': 'Info:',
            'name': 'info',
            'type': 'str',
            'value': 'Nothing',
            'readonly': True
        }]

    desc = {'Pressure': "Lecture en 0.01 près"}

    def ini_attributes(self):
        self.controller: CellKraftE1500Drivers
        self.settings.child('info').setValue(self.desc['Pressure'])
        pass

    def commit_settings(self, param: Parameter):
        """Apply the consequences of a change of value in the detector settings

        Parameters
        ----------
        param: Parameter
            A given parameter (within detector_settings) whose value has been changed by the user
        """
        pass

    def ini_detector(self, controller=None):
        """Actuator communication initialization

        Parameters
        ----------
        controller: (object)
            custom object of a PyMoDAQ plugin (Slave case). None if only one actuator by controller (Master case)

        Returns
        -------
        info: str
        initialized: bool
            False if initialization failed otherwise True
        """

        if self.is_master:  # Master Case : controller == None
            controller = CellKraftE1500Drivers(self.settings['host'])  # Create control
            self.controller = controller
            initialized = self.controller.init_hardware()  # Init connection
            info = "Initialized in Master"

        else:  # Slave Case : controller != None
            self.controller = self.ini_detector_init(slave_controller=controller)
            initialized = self.controller.instr.connected
            info = "Initialized in Slave"

        return info, initialized

    def close(self):
        """Terminate the communication protocol"""
        self.controller.close()
        logger.info("Communication ended successfully")

    def grab_data(self, Naverage=1, live=False, **kwargs):
        """Start a grab from the detector

        Parameters
        ----------
        Naverage: int
            Number of hardware averaging (if hardware averaging is possible, self.hardware_averaging should be set to
            True in class preamble, and you should code this implementation)
        kwargs: dict
            others optionals arguments
        """
        data_tot = self.controller.Get_Pressure()
        self.dte_signal.emit(
            DataToExport(name='Graph',
                         data=[DataFromPlugins(
                            name='Pressure',
                            data=data_tot,
                            dim='Data0D',
                            labels=['Pressure in bar'])
                            ]
                         )
            )

    def stop(self):
        """Stop the current grab hardware wise if necessary"""
        return ''

if __name__ == '__main__':
    main(__file__, True)