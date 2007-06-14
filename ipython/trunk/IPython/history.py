# -*- coding: utf-8 -*-

""" History related magics and functionality """

import fnmatch

def magic_history(self, parameter_s = ''):
    """Print input history (_i<n> variables), with most recent last.
    
    %history       -> print at most 40 inputs (some may be multi-line)\\
    %history n     -> print at most n inputs\\
    %history n1 n2 -> print inputs between n1 and n2 (n2 not included)\\
    
    Each input's number <n> is shown, and is accessible as the
    automatically generated variable _i<n>.  Multi-line statements are
    printed starting at a new line for easy copy/paste.
    

    Options:

      -n: do NOT print line numbers. This is useful if you want to get a
      printout of many lines which can be directly pasted into a text
      editor.

      This feature is only available if numbered prompts are in use.

      -t: print the 'translated' history, as IPython understands it. IPython
      filters your input and converts it all into valid Python source before
      executing it (things like magics or aliases are turned into function
      calls, for example). With this option, you'll see the native history
      instead of the user-entered version: '%cd /' will be seen as
      '_ip.magic("%cd /")' instead of '%cd /'.
      
      -g: treat the arg as a pattern to grep for in (full) history
      
      -s: show "shadow" history
    """

    ip = self.api
    shell = self.shell
    if not shell.outputcache.do_full_cache:
        print 'This feature is only available if numbered prompts are in use.'
        return
    opts,args = self.parse_options(parameter_s,'gnts',mode='list')

    if not opts.has_key('t'):
        input_hist = shell.input_hist_raw
    else:
        input_hist = shell.input_hist
    
    default_length = 40
    pattern = None
    if opts.has_key('g'):
        init = 1
        final = len(input_hist)
        head, pattern = parameter_s.split(None,1)
        pattern = "*" + pattern + "*"
    elif len(args) == 0:
        final = len(input_hist)
        init = max(1,final-default_length)
    elif len(args) == 1:
        final = len(input_hist)
        init = max(1,final-int(args[0]))
    elif len(args) == 2:
        init,final = map(int,args)
    else:
        warn('%hist takes 0, 1 or 2 arguments separated by spaces.')
        print self.magic_hist.__doc__
        return
    width = len(str(final))
    line_sep = ['','\n']
    print_nums = not opts.has_key('n')
    
    found = False
    if pattern is not None:
        sh = ip.IP.shadowhist.all()
        for idx, s in sh:
            if fnmatch.fnmatch(s, pattern):
                print "0%d: %s" %(idx, s)
                found = True
    
    if found:
        print "==="
        print "^shadow history ends, fetch by %rep <number> (must start with 0)"
        print "=== start of normal history ==="
        
    for in_num in range(init,final):        
        inline = input_hist[in_num]
        if pattern is not None and not fnmatch.fnmatch(inline, pattern):
            continue
            
        multiline = int(inline.count('\n') > 1)
        if print_nums:
            print '%s:%s' % (str(in_num).ljust(width),line_sep[multiline]),
        print inline,



def magic_hist(self, parameter_s=''):
    """Alternate name for %history."""
    return self.magic_history(parameter_s)



def rep_f(self, arg):
    r""" Repeat a command, or get command to input line for editing

    - %rep (no arguments):
    
    Place a string version of last input to the next input prompt. Allows you
    to create elaborate command lines without using copy-paste::
    
        $ l = ["hei", "vaan"]       
        $ "".join(l)        
        ==> heivaan        
        $ %rep        
        $ heivaan_ <== cursor blinking    
    
    %rep 45
    
    Place history line 45 to next input prompt. Use %hist to find out the number.
    
    %rep 1-4 6-7 3
    
    Repeat the specified lines immediately. Input slice syntax is the same as
    in %macro and %save.
    
    """
    
    
    opts,args = self.parse_options(arg,'',mode='list')
    ip = self.api    
    if not args:
        ip.set_next_input(str(ip.user_ns["_"]))
        return

    if len(args) == 1:
        arg = args[0]
        if len(arg) > 1 and arg.startswith('0'):
            # get from shadow hist
            num = int(arg[1:])
            line = self.shadowhist.get(num)
            ip.set_next_input(str(line))
            return
        try:
            num = int(args[0])
            ip.set_next_input(str(ip.IP.input_hist_raw[num]).rstrip())
            return
        except ValueError:
            pass
        

    lines = self.extract_input_slices(args, True)
    print "lines",lines
    ip.runlines(lines)


_sentinel = object()

class ShadowHist:
    def __init__(self,db):
        # cmd => idx mapping
        self.curidx = 0
        self.db = db
    
    def inc_idx(self):
        idx = self.db.get('shadowhist_idx', 1)
        self.db['shadowhist_idx'] = idx + 1
        return idx
        
    def add(self, ent):
        old = self.db.hget('shadowhist', ent, _sentinel)
        if old is not _sentinel:
            return
        newidx = self.inc_idx()
        #print "new",newidx # dbg
        self.db.hset('shadowhist',ent, newidx)
    
    def all(self):
        d = self.db.hdict('shadowhist')
        items = [(i,s) for (s,i) in d.items()]
        items.sort()
        return items

    def get(self, idx):
        all = self.all()
        
        for k, v in all:
            #print k,v
            if k == idx:
                return v

def test_shist():
    from IPython.Extensions import pickleshare
    db = pickleshare.PickleShareDB('~/shist')
    s = ShadowHist(db)
    s.add('hello')
    s.add('world')
    s.add('hello')
    s.add('hello')
    s.add('karhu')
    print "all",s.all()
    print s.get(2)

def init_ipython(ip):
    ip.expose_magic("rep",rep_f)        
    ip.expose_magic("hist",magic_hist)            
    ip.expose_magic("history",magic_history)
    
#test_shist()
