import IPython.ipapi
ip = IPython.ipapi.get()

import os,pprint

def export(filename = None):

    lines = ['import IPython.ipapi', 'ip = IPython.ipapi.get()','']

    vars = ip.db.keys('autorestore/*')
    vars.sort()
    varstomove = []
    get = ip.db.get
    
    macros = []
    variables = []
    
    for var in vars:
        k = os.path.basename(var)
        v = get(var)

        if k.startswith('_'):
            continue
        if isinstance(v, IPython.macro.Macro):
            macros.append((k,v))
        if type(v) in [int, str, float]:
            variables.append((k,v))
            
            

    if macros:
        lines.extend(['# === Macros ===' ,''])
    for k,v in macros:
        lines.append("ip.defmacro('%s'," % k)
        for line in v.value.splitlines():
            lines.append(' ' + repr(line+'\n'))
        lines.extend([')', ''])
        
    if variables:
        lines.extend(['','# === Variables ===',''])
        for k,v in variables:
            varstomove.append(k)
            lines.append('%s = %s' % (k,repr(v)))
                
        lines.append('ip.to_user_ns("%s")' % (' '.join(varstomove)))
    
    bkms = ip.db.get('bookmarks',{})
    
    if bkms:
        lines.extend(['','# === Bookmarks ===',''])
        lines.append("ip.db['bookmarks'] = %s " % pprint.pformat(bkms, indent = 2) )
        
    aliases = ip.db.get('stored_aliases', {} )
    
    if aliases:
        lines.extend(['','# === Alias definitions ===',''])
        for k,v in aliases.items():
            lines.append("ip.defalias('%s', %s)" % (k, repr(v[1])))

    env = ip.db.get('stored_env')
    if env:
        lines.extend(['','# === Stored env vars ===',''])
        lines.append("ip.db['stored_env'] = %s " % pprint.pformat(env, indent = 2) )
        
    
    
    out = '\n'.join(lines)
    
    if filename:
        open(filename,'w').write(out)
    else:
        print out
    
