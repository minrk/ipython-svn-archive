"""testtools.py - tools for automatic varification.

The functions here are supposed to add automatic verrification to functions.
The most useful verifier at the moment is reverse_verifier"""

import inspect

def redefine_function(func, body, global_dict = {}):
    """Returns a new function with the same arguments and document string as
    'func' but with a new body. 'body' must be a string with no indentation at
    the main level. You can use the function's name to address the function.
    In body, as a convenience, you can use %(__callstring)s which will be
    replaced with the argument list of 'func' You will also have access to the
    variables in 'global_dict'"""

    loc = {'__builtins__':__import__('__builtin__', globals(), locals(),[]), 
           func.func_name:func}
    loc.update(global_dict)
    
    spec = inspect.getargspec(func)
    fspec = inspect.formatargspec(*spec)
    body = '\n    '.join(body.splitlines())
    callstring = ','.join(spec[0])
    if spec[1] is not None:
        callstring+=',*'+spec[1]
    if spec[2] is not None:
        callstring+=',**'+spec[2]
    loc['__callstring'] = callstring
    __callstring = callstring
    s = """
def __new_func%%(fspec)s:
    %(body)s
""" % locals()
    s = s%locals()
    exec s in loc, loc
    new_func = loc['__new_func']
    new_func.func_name = func.func_name
    new_func.__doc__ = func.__doc__
    return new_func

def simple_chain_elem(string):
    """Creates a chain element with a function which returns the result of
    evaluatign the given string. For example 
    simple_chain_elem('{'x':x}') returns an element equivalent to:
    {'f':lambda x:{'x':x}, 'direct_output':True}
    """

    def __f(**__kwds):
        for __key in __kwds.keys():
            exec "%s = __kwds[__key]"%__key in globals(), locals()
        del __kwds, __key
        return eval(string)
    return {'f':__f, 'save_result':False, 'direct_output':True}

def function_chain_elem(func):
    """For 'func' creates the chain_element:
    {'f':func, 'direct_output':False}
    """
    return {'f':func, 'direct_output':False}

def chain(func, name, seq):
    """Creates a new chain associated with 'func'. 'name' is the name of the
    chain. It must be a valid variable name. 'seq' is a sequence describing the chain
    
    A chain is a sequence of functions with the property that the output of
    one function is the input to the next one. Each function should either
    return the dictionary or set the 'direct_output' parameter to False in
    which case a dictionary is created automatically. The dictionary is used
    as the argument list of the next function. Therefore only the first
    function in a chain cah have variable number of unnamed arguments. The arguments of 
    the first function must be the same as the arguments of 'func'

    Each element in 'seq' describes one element in the chain. The most general
    element is a dictionary of the type:

        {'f':function, 'direct_output':True, 'save_result':False}. 

    Here 'f' points to the actual function in the chain and is the only
    mandatory key in the dictionary. If 'f' is None then 'func' is used as the
    function.

    If 'direct_output' is True the return value of the function is used as
    the argument list of the next function. If 'direct_output' is False, the
    argument list of the next function consists of all the arguments of
    function and an additional argument '__result' which contains the result
    of the function execution. If function modified any of its arguments the
    modifued values will be passed to the next function. The default value for
    'direct_output' is True
    
    If 'save_result' is True the return value is saved and is used as the
    return value of the verified function. The default value for save_result
    is False. You should set this to True in only one element in one chain on
    a function.

    The elements is 'seq' can also be either strings or functions. In that
    case simple_chain_elem or function_chain_elem are called to get the actual
    chain element."""

    verified = False
    if func.func_dict.get('verified', False):
        verified = True
        func_ver = func
        func = func.func_orig

    if func.func_dict.get('chain',None) is None:
        func.chain = {}

    chn = []
    for elem in seq:
        if isinstance(elem, str) or isinstance(elem, unicode):
            elem = simple_chain_elem(elem)
        elif callable(elem):
            elem = function_chain_elem(elem)
        elif elem is None:
            elem = function_chain_elem(func)
        f = elem['f']
        if f is None:
            f=func

        if not elem.get('direct_output',True):
            f = redefine_function(f, """
__result = %s(%%(__callstring)s)
return locals()
"""%f.func_name)
            def result(arg):
                return arg['__result']
        else:
            def result(arg):
                return arg

        if not elem.get('save_result', False) :
            result = None

        chn.append((f, result, elem.get('single_argument',False)))
    func.chain[name] = chn
  
def function_verifier(func, ch_names_seq, func_ver):
    """Adds a generic function verifier to 'func'
    
    ch_names_seq is a sequence of chain names and func_ver is a function. When
    this varifier is run each of the chains in ch_name_seq are run and the
    results are passed as arguments to 'func_ver' in the order in which they
    were given in 'ch_names_seq'"""
    
    
    verified = False
    if func.func_dict.get('verified', False):
        verified = True
        func_ver = func
        func = func.func_orig
    verifiers = func.func_dict.get('verifiers', [])
    verifiers.append((func_ver, ch_names_seq))
    func.verifiers = verifiers

def predicate_verifier(func, ch_names_seq, preds, before_all="", after_all=""):
    """Creates a function verifier from the given strings and adds it to 'func'.
    
    Here 'ch_names_seq' has the same meaning as in function_verifier. 'preds'
    is a sequence of strings. In the created function each string is evaluated
    and if the return value is False an Assert exception is raised.
    'before_all' can contain code which is executed before all predicares are
    evaluated and 'after_all' is executed after the predicated are evaluated.
    In each of these code blocks you can use the chain names to get their values"""
    
    callstring = 'def __tmp_func(%s):\n    '%','.join(ch_names_seq)
    pred_lst = ["""assert %s, \"\"\"%s\"\"\""""%(str(x),str(x)) for x in preds]
    before_lst = before_all.splitlines()
    after_lst = after_all.splitlines()
    body = '\n    '.join(before_lst+pred_lst+after_lst)
    func_string = callstring+body
    exec func_string in globals(), locals()
    return function_verifier(func, ch_names_seq, __tmp_func)

def run_chain(chain, values):
    """Runs a chain. 'values' contains the arguments of the first function"""
    #does not support single_argument, nor *args in functions in the
    #chain except the first one
    #args = [values[3][x] for x in values[0]]
    args = []
    if values[1] is not None:
        args.extend(values[3][values[1]])
    kwds = dict((x, values[3][x]) for x in values[0])
    if values[2] is not None:
        kwds.update(values[3][values[2]])

    __result = None
    kwds = chain[0][0](*args, **kwds)
    if chain[0][1] is not None:
        __result = chain[0][1](kwds)

    for elem in chain[1:]:
        kwds = elem[0](**kwds)
        if elem[1] is not None:
            __result = elem[1](kwds)
    return kwds, __result
    
def __verify(func_orig, values): 
    verifiers = func_orig.func_dict.get('verifiers',[])
    chain_values = {}
    last_ch_name = None
    for verifier in verifiers:
        for ch_name in [x for x in verifier[1] if x not in chain_values.keys()]:
            flag = False
            for elem in func_orig.chain[ch_name]:
                if elem[1] is not None and last_ch_name is None:
                    flag = True
                    last_ch_name = ch_name
                    break
            if flag:
                continue
            chain_values[ch_name], tmp = run_chain(func_orig.chain[ch_name],values)

    result = None
    if last_ch_name is not None:
        chain_values[last_ch_name], result = run_chain(func_orig.chain[last_ch_name], values)
    for verifier in verifiers:
        args = []
        for ch_name in verifier[1]:
            args.append(chain_values[ch_name])
        verifier[0](*args)
    return result

def verify(func):
    """Returns a verified function. You can add all the chains and
    varifiers either before or after calling verify"""
    func_orig = func
    func_new = redefine_function(func,"""
__fr = __inspect.currentframe()
__values = __inspect.getargvalues(__fr)

return __verify(%s,__values)
"""%func.func_name, {'__verify':__verify, '__inspect':inspect})
    func_new.verified = True
    func_new.func_orig = func_orig
    return func_new


uniq = 0
def reverse_verifier(func, rev_func, prestring, midstring, poststring):
    """Creates a verifier of 'func' using its reverse function 'rev_func'
    
    The general idea here is to check if x == rev_func(func(x)). That is not
    so simple in more complex situations. For example if 'func' and 'rev_func'
    are methods modifying an object in order to check the condition you could
    write code of the kind: 
    old_obj = copy.deepcopy(obj)
    func(obj,parameters)
    rev_func(obj,reverse_parameters)
    assert obj==old_obj

    'reverse_verifier' generalizes those situations. 'prestring', 'midstring'
    and 'poststring' must be strings of code. In prestring you can use the
    arguments of 'func' which will be in their original values. 'midstring'
    can use the arguments of 'func' which, if mutable, might be modified by
    'func'. 'midstring' can also use an additional argument '__result' which
    will contain the return value of 'func'. The result of evaluating
    'midstring' must be a dictionary which will be used as the argument list
    of 'rev_func' 'poststring' is evaluated after 'rev_func' is called. it can
    use the arguments of 'rev_func', which could be modified, and '__result'
    which will contain the result of 'rev_func'. If the two functions worked
    correctly the values of 'prestring' and 'poststring' must match. After all
    funcitons and strings are run 'func' is run for the second time and its
    result is returned by the verified function
    
    Example:

    def a(x,y):
        return x+y

    def b(x,y):
        return x-y

    reverse_verifier(a, b, 'x',"{'x':__result, 'y':y}", '__result')
    reverse_verifier(a, b, 'y',"{'x':__result, 'y':x}", '__result')
    
    a = verify(a)
    
    In this example whenever 'a' is run the verifiers will check that
    
    x == b(a(x,y),y) and
    y == b(a(x,y),x)

    """

    global uniq
    a_name = 'A%d'%uniq
    b_name = 'B%d'%uniq
    uniq+=1
    chain(func, a_name, [prestring])
    chain(func, b_name, [{'f':None, 'direct_output':False}, midstring,
                         {'f':rev_func, 'direct_output':False}, poststring])

    if not func.chain.has_key('__result'):
        chain(func, '__result',[{'f':None, 'save_result':True}])
    return predicate_verifier(func,(a_name, b_name,'__result'),('%s==%s'%(a_name,b_name),))

def reverse_decorator(rev_func, prestring, midstring, poststring):
    """A decorator which does the same as reverse_verifier"""
    
    def f(func):
        reverse_verifier(func, rev_func, prestring, midstring, poststring)
        return func
    
    return f

