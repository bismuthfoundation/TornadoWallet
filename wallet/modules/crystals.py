"""
Crystals manager, based upon Bismuth plugins, MIT Licence.
Copyright 2013, Michael E. Cotterell
Copyright 2018, EggPool
Copyright 2018, BismuthFoundation
"""


import importlib
import importlib.util
import importlib.machinery
import os
import logging
import collections
import sys
from modules import helpers


__version__ = '0.2'


class CrystalManager:
    """
    A simple plugin aka crystals manager
    """

    def __init__(self, app_log=None, main_module='__init__', crystal_folder='', verbose=True, init=False):
        if app_log:
            self.app_log = app_log
        else:
            logging.basicConfig(level=logging.DEBUG)
            self.app_log = logging
        if crystal_folder == '':
            crystal_folder = os.path.join(helpers.base_path(), 'crystals')
        self.crystal_folder = crystal_folder
        self.main_module = main_module
        self.verbose = verbose
        self.available_crystals = self.get_available_crystals()
        if self.verbose:
            self.app_log.info("Available crystals: {}".format(', '.join(self.available_crystals.keys())))
        self.loaded_crystals = collections.OrderedDict({})
        if init:
            self.init()

    def init(self):
        """
        loads all available crystals and inits them.
        :return:
        """
        for crystal in self.available_crystals:
            # TODO: only load "auto load" crystals
            self.load_crystal(crystal)
        self.execute_action_hook('init', {'manager': self})

    def get_available_crystals(self):
        """
        Returns a dictionary of crystals available in the crystals folder
        """
        crystals = collections.OrderedDict({})
        try:
            for possible in sorted(os.listdir(self.crystal_folder)):
                location = os.path.join(self.crystal_folder, possible)
                if os.path.isdir(location) and self.main_module + '.py' in os.listdir(location):
                    info = importlib.machinery.PathFinder().find_spec(self.main_module, [location])
                    crystals[possible] = {
                        'name': possible,
                        'info': info,
                        'autoload': True  # Todo
                    }
        except Exception as e:
            self.app_log.info("Can't list crystals from '{}'.".format(self.crystal_folder))
        # TODO: sort by name or priority, add json specs file.
        return crystals

    def get_loaded_crystals(self):
        """
        Returns a dictionary of the loaded crystal modules
        """
        return self.loaded_crystals.copy()

    def load_crystal(self, crystal_name):
        """
        Loads a crystal module
        """
        if crystal_name in self.available_crystals:
            if crystal_name not in self.loaded_crystals:
                spec = self.available_crystals[crystal_name]['info']
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                self.loaded_crystals[crystal_name] = {
                    'name': crystal_name,
                    'info': self.available_crystals[crystal_name]['info'],
                    'module': module
                }
                if self.verbose:
                    self.app_log.info("Crystal '{}' loaded".format(crystal_name))
            else:
                self.app_log.warning("Crystal '{}' already loaded".format(crystal_name))
        else:
            self.app_log.error("Cannot locate crystal '{}'".format(crystal_name))
            raise Exception("Cannot locate crystal '{}'".format(crystal_name))

    def _unload_crystal(self, crystal_name):
        del self.loaded_crystals[crystal_name]
        if self.verbose:
            self.app_log.info("Crystal '{}' unloaded".format(crystal_name))

    def unload_crystal(self, crystal_name=''):
        """
        Unloads a single crystal module or all if crystal_name is empty
        """
        try:
            if crystal_name:
                self.unload_crystal(crystal_name)
            else:
                for crystal in self.get_loaded_crystals():
                    self._unload_crystal(crystal)
        except:
            pass

    def get_handlers(self):
        handlers = []
        for key, crystal_info in self.loaded_crystals.items():
            try:
                module = crystal_info['module']
                name = key.split('_')[1]
                hook_func_name ="{}Handler".format( name.capitalize())
                # print(key, "hook_func_name", hook_func_name)
                if hasattr(module, hook_func_name):
                    hook_class = getattr(module, hook_func_name)
                    handlers.append((r"/crystal/{}/(.*)".format(name), hook_class))

            except Exception as e:
                self.app_log.warning("Crystal '{}' exception '{}' on get_handlers".format(key, e))
        return handlers

    def execute_action_hook(self, hook_name, hook_params=None, first_only=False):
        """
        Executes action hook functions of the form action_hook_name contained in
        the loaded crystal modules.
        """
        for key, crystal_info in self.loaded_crystals.items():
            try:
                module = crystal_info['module']
                hook_func_name = "action_{}".format(hook_name)
                if hasattr(module, hook_func_name):
                    hook_func = getattr(module, hook_func_name)
                    hook_func(hook_params)
                    if first_only:
                        # Avoid deadlocks on specific use cases
                        return
            except Exception as e:
                self.app_log.warning("Crystal '{}' exception '{}' on action '{}'".format(key, e, hook_name))

    def execute_filter_hook(self, hook_name, hook_params, first_only=False):
        """
        Filters the hook_params through filter hook functions of the form
        filter_hook_name contained in the loaded crystal modules.
        """
        try:
            hook_params_keys = hook_params.keys()
            for key, crystal_info in self.loaded_crystals.items():
                try:
                    module = crystal_info['module']
                    hook_func_name = "filter_{}".format(hook_name)
                    print("looking for ", hook_func_name)
                    if hasattr(module, hook_func_name):
                        hook_func = getattr(module, hook_func_name)
                        print("hook_params", hook_params)
                        hook_params = hook_func(hook_params)
                        for nkey in hook_params_keys:
                            if nkey not in hook_params.keys():
                                msg = "Function '{}' in crystal '{}' is missing '{}' in the dict it returns".format(
                                    hook_func_name, crystal_info['name'], nkey)
                                self.app_log.error(msg)
                                raise Exception(msg)
                            if first_only:
                                # Avoid deadlocks on specific use cases
                                return  # will trigger the finally section
                except Exception as e:
                    self.app_log.warning("Crystal '{}' exception '{}' on filter '{}'".format(key, e, hook_name))
                    exc_type, exc_obj, exc_tb = sys.exc_info()
                    fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                    print(exc_type, fname, exc_tb.tb_lineno)

        except Exception as e:
            self.app_log.warning("Exception '{}' on filter '{}'".format(e, hook_name))
        finally:
            return hook_params


if __name__ == "__main__":
    print("This is the Crystals module.")
