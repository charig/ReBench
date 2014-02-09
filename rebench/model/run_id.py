from numbers import Number
import logging
import os
import re
import sys


class RunId:
    _registry = {}
    
    @classmethod
    def reset(cls):
        cls._registry = {}
    
    @classmethod
    def create(cls, cfg, variables, terminationCriterion='total'):
        run = RunId(cfg, variables, terminationCriterion)
        if run in RunId._registry:
            return RunId._registry[run]
        else:
            RunId._registry[run] = run
            return run
    
    def __init__(self, cfg, variables, terminationCriterion='total'):
        self._cfg = cfg
        self._variables = self._stringify(variables)
        self._criterion = 'total'
    
    @property
    def cfg(self):
        return self._cfg
    
    @property
    def variables(self):
        return self._variables
    
    @property
    def criterion(self):
        return self._criterion
    
    def __hash__(self):
        return (hash(self._cfg) ^ 
                hash(self._variables) ^ 
                hash(self._criterion))
        
    def _stringify(self, aTuple):
        result = ()
        for item in aTuple:
            if isinstance(item, Number) or item is None:
                result += (str(item), )
            else:
                result += (item, )
                
        return result
    
    def as_simple_string(self):
        return "%s %s %s" % (self._cfg.as_simple_string(), self._variables, self._criterion)
    
    def as_tuple(self):
        return self._cfg.as_tuple() + self._variables + (self._criterion, )
    
    def cmdline(self):
        cmdline  = ""
                
        vm_cmd = "%s/%s %s" % (os.path.abspath(self._cfg.vm['path']),
                               self._cfg.vm['binary'],
                               self._cfg.vm.get('args', ''))
            
        cmdline += vm_cmd 
        cmdline += self._cfg.suite['command']
        
        if self._cfg.extra_args is not None:
            cmdline += " %s" % (self._cfg.extra_args or "")
            
        (cores, input_size, var_val) = self._variables

        try:
            cmdline = cmdline % {'benchmark':self._cfg.name, 'input':input_size, 'variable':var_val, 'cores' : cores}
        except ValueError:
            self._report_cmdline_format_issue_and_exit(cmdline)
        except TypeError:
            self._report_cmdline_format_issue_and_exit(cmdline)
        
        return cmdline.strip()
    
    def __eq__(self, other):
        return (isinstance(other, self.__class__)
            and self.cmdline() == other.cmdline())

    def __ne__(self, other):
        return not self.__eq__(other)
    
    def _report_cmdline_format_issue_and_exit(self, cmdline):
        logging.critical("The configuration of %s contains improper Python format strings.", self._cfg.name)
         
        # figure out which format misses a conversion type
        without_conversion_type = re.findall("\%\(.*?\)(?![diouxXeEfFgGcrs\%])", cmdline)
        logging.error("The command line configured is: %s", cmdline)
        logging.error("The following elements do not have conversion types: \"%s\"",
                      '", "'.join(without_conversion_type))
        logging.error("This can be fixed by replacing for instance %s with %ss",
                      without_conversion_type[0],
                      without_conversion_type[0])
        sys.exit(-1)