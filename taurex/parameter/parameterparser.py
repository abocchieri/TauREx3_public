import configobj
from taurex.log import Logger
from .factory import *

class ParameterParser(Logger):

    def __init__(self):
        super().__init__('ParamParser')
        self._read = False
    

    def transform(self,section,key):
        val = section[key]
        newval = val
        if isinstance(val,list):
            try:
                newval = list(map(float,val))

            except:
                pass
        elif isinstance(val, (str)):
            if val.lower() in ['true',  'yes', 'yeah', 'yup', 'certainly', 'uh-huh',]:
                newval = True
            elif val.lower() in ['false',  'no', 'nope', 'no-way', 'hell-no', 'fuck-off']:
                newval = False
            else:
                try:
                    newval = float(val)
                except:
                    pass
        section[key]=newval
        return newval


    def setup_globals(self):
        from taurex.cache import CIACache,OpacityCache
        config = self._raw_config.dict()
        if 'Global' in config:
            try:
                OpacityCache().set_opacity_path(config['Global']['xsec_path'])
            except KeyError:
                self.warning('No xsec path set, opacities cannot be used in model')
            try:
                
                OpacityCache().set_interpolation(config['Global']['xsec_interpolation'])
                self.info('Interpolation mode set to {}'.format(config['Global']['xsec_interpolation']))
            except KeyError:
                self.info('Interpolation mode set to linear')

            try:
                CIACache().set_cia_path(config['Global']['cia_path'])
            except KeyError:
                self.warning('No cia path set, cia cannot be used in model')



    def read(self,filename):
        import os.path
        if not os.path.isfile(filename):
            raise Exception('Input file {} does not exist'.format(filename))
        self._raw_config = configobj.ConfigObj(filename)
        self.debug('Raw Config file is {}, filename is {}'.format(self._raw_config,filename))
        self._raw_config.walk(self.transform)
        config = self._raw_config.dict()
        self.debug('Config file is {}, filename is {}'.format(config,filename))


    def generate_optimizer(self):
        config = self._raw_config.dict()
        if 'Optimizer' in config:
            return create_optimizer(config['Optimizer'])
        else:
            None

    def generate_spectrum(self):
        import numpy as np

        config = self._raw_config.dict()
        observed = None
        if 'Spectrum' in config:
            spectrum_config = config['Spectrum']
            if 'observed_spectrum' in spectrum_config:
                from taurex.data.spectrum.observed import ObservedSpectrum
                observed = ObservedSpectrum(spectrum_config['observed_spectrum'])

            if 'grid_type' in spectrum_config:
                grid_type = spectrum_config['grid_type']

                if grid_type == 'observed':
                    if observed is not None:
                        return observed,observed.wavenumberGrid
                    else:
                        self.critical('grid type is observed yet no observed_spectrum is defined!!!')
                        raise Exception('No observed spectrum defined for observed grid_type')
                elif grid_type == 'native':
                    return observed,None
                elif grid_type == 'manual':

                    if 'wavenumber_grid' in spectrum_config:
                        start,end,size = spectrum_config['wavenumber_grid']
                        return observed,np.linspace(start,end,int(size))
                    elif 'wavelength_grid' in spectrum_config:
                        start,end,size = spectrum_config['wavelength_grid']
                        return observed,10000/np.linspace(start,end,int(size))
                    else:
                       self.critical('grid type is manual yet neither wavelength_grid or wavenumber_grid is defined')
                       raise Exception('wavenumber_grid/wavelength_grid not defined in input for manual grid_type')
                else:
                    return observed,None

    def generate_model(self):
        config = self._raw_config.dict()
        if 'Model' in config:
            chemistry = self.generate_chemistry_profile()
            pressure = self.generate_pressure_profile()
            temperature = self.generate_temperature_profile()
            planet = self.generate_planet()
            star = self.generate_star()
            model= create_model(config['Model'],chemistry,temperature,pressure,planet,star)
        else:
            return None
        
        return model
    def generate_chemistry_profile(self):
        config = self._raw_config.dict()
        if 'Chemistry' in config:
            return create_chemistry(config['Chemistry'])
        else:
            return None

    def generate_pressure_profile(self):
        config = self._raw_config.dict()
        if 'Pressure' in config:
            return create_pressure_profile(config['Pressure'])
        else:
            return None
    
    def generate_temperature_profile(self):
        config = self._raw_config.dict()
        if 'Temperature' in config:
            return create_temperature_profile(config['Temperature'])
        else:
            return None
    
    def generate_planet(self):
        config = self._raw_config.dict()

        if 'Planet' in config:
            from taurex.data.planet import Planet
            return create_klass(config['Planet'],Planet)
        else:
            return None
    def generate_star(self):
        config = self._raw_config.dict()
        
        if 'Star' in config:
            return create_star(config['Star'])
        else:
            return None


    def generate_fitting_parameters(self):
        config = self._raw_config.dict()
        if 'Fitting' in config:
            fitting_config = config['Fitting']

            fitting_params = {}

            for key,value in fitting_config.items():
                fit_param,fit_type=key.split(':')
                if not fit_param in fitting_params:
                    fitting_params[fit_param] = {'fit':None,'bounds':None,'mode':None}
                fitting_params[fit_param][fit_type]=value
        
        return fitting_params

