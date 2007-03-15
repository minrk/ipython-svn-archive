from rlmain import *

rl = Readline()

def GetOutputFile():
    '''Return the console object used by readline so that it can be used for printing in color.'''
    return rl.console

# make these available so this looks like the python readline module
parse_and_bind = rl.parse_and_bind
get_line_buffer = rl.get_line_buffer
insert_text = rl.insert_text
read_init_file = rl.read_init_file
read_history_file = rl.read_history_file
write_history_file = rl.write_history_file
get_history_length = rl.get_history_length
set_history_length = rl.set_history_length
set_startup_hook = rl.set_startup_hook
set_pre_input_hook = rl.set_pre_input_hook
set_completer = rl.set_completer
get_completer = rl.get_completer
get_begidx = rl.get_begidx
get_endidx = rl.get_endidx
set_completer_delims = rl.set_completer_delims
get_completer_delims = rl.get_completer_delims
add_history = rl.add_history

if __name__ == '__main__':
    res = [ rl.readline('In[%d] ' % i) for i in range(3) ]
    print res
else:
    console.install_readline(rl.readline)

