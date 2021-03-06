# -*- coding: UTF-8 -*-
#this file is needed in site-packages to emulate readline
#necessary for rlcompleter since it relies on the existance
#of a readline module



import pyreadline.rlmain
from pyreadline.init_rl import *

__all__ = [ 'parse_and_bind',
            'get_line_buffer',
            'insert_text',
            'read_init_file',
            'read_history_file',
            'write_history_file',
            'get_history_length',
            'set_history_length',
            'set_startup_hook',
            'set_pre_input_hook',
            'set_completer',
            'get_completer',
            'get_begidx',
            'get_endidx',
            'set_completer_delims',
            'get_completer_delims',
            'add_history',
            'GetOutputFile']
