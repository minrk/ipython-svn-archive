# -*- coding: iso-8859-1 -*-
"""
Classes for handling input/output prompts.

$Id$
"""
from __future__ import nested_scopes

#*****************************************************************************
#       Copyright (C) 2001 Fernando Pérez. <fperez@colorado.edu>
#
#  Distributed under the terms of the GNU Lesser General Public License (LGPL)
#
#    This code is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
#    Lesser General Public License for more details.
#
#  The full text of the LGPL is available at:
#
#                  http://www.gnu.org/copyleft/lesser.html
#*****************************************************************************

import Release
__version__ = Release.version
__date__    = Release.date
__author__  = '%s <%s>' % Release.authors['Fernando']
__license__ = Release.license

#****************************************************************************
# Required modules
import os,sys
from pprint import pprint,pformat

# Homebrewed
from genutils import *
from Struct import Struct
import ultraTB
from ColorANSI import *
from Magic import Macro
from Itpl import Itpl

#****************************************************************************
#Color schemes for Prompts.

PromptColors = ColorSchemeTable()
InputColors = ultraTB.InputTermColors  # just a shorthand
Colors = ultraTB.TermColors  # just a shorthand

PromptColors.add_scheme(ColorScheme(
    'NoColor',
    in_prompt = InputColors.NoColor,  # Input prompt
    in_number = InputColors.NoColor,  # Input prompt number
    in_prompt2 = InputColors.NoColor, # Continuation prompt
    in_normal = InputColors.NoColor,  # color off (usu. Colors.Normal)
    
    out_prompt = Colors.NoColor, # Output prompt
    out_number = Colors.NoColor, # Output prompt number

    normal = Colors.NoColor  # color off (usu. Colors.Normal)
    ))
# make some schemes as instances so we can copy them for modification easily:
__PColLinux =  ColorScheme(
    'Linux',
    in_prompt = InputColors.Green,
    in_number = InputColors.LightGreen,
    in_prompt2 = InputColors.Green,
    in_normal = InputColors.Normal,  # color off (usu. Colors.Normal)

    out_prompt = Colors.Red,
    out_number = Colors.LightRed,

    normal = Colors.Normal
    )
# Don't forget to enter it into the table!
PromptColors.add_scheme(__PColLinux)
# Slightly modified Linux for light backgrounds
__PColLightBG = ColorScheme('LightBG',**__PColLinux.colors.dict().copy())

__PColLightBG.colors.update(
    in_prompt = InputColors.Blue,
    in_number = InputColors.LightBlue,
    in_prompt2 = InputColors.Blue
)
PromptColors.add_scheme(__PColLightBG)

del Colors


#-----------------------------------------------------------------------------
class Prompt1:
    """Interactive prompt similar to Mathematica's."""

    def __init__(self,cache,colors='NoColor',input_sep = '\n',prompt = 'In [%n]:'):
        self.cache = cache
        self.input_sep = input_sep

        # Set colors
        self.color_table = PromptColors
        self.color_table.set_active_scheme(colors)
        Colors = self.color_table.active_colors # shorthand
        self.col_p = Colors.in_prompt
        self.col_num = Colors.in_number
        self.col_norm = Colors.in_normal
        self.col_norm_ni = Colors.normal
        # We need a non-input version of this escape for the '--->'
        # auto-call prompts used in the auto_rewrite() method.
        self.col_p_ni = self.col_p.replace('\001','').replace('\002','') 

        # Set template to create each actual prompt (where numbers change)
        self.p_template = prompt.replace('%n','%s') + ' '
        self.p_str = Itpl('$self.input_sep${self.col_p}' +
                          self.p_template.replace('%s','$self.col_num'
                                                  '$self.cache.prompt_count'
                                                  '$self.col_p') +
                          '$self.col_norm')

    def __str__(self):
        self.cache.prompt_count += 1
        return str(self.p_str)

    def auto_rewrite(self):
        """Print a string of the form '--->' which lines up with the previous
        input string. Useful for systems which re-write the user input when
        handling automatically special syntaxes."""

        curr = self.p_template.replace('%s',str(self.cache.prompt_count))
        return self.col_p_ni + '-'*(len(curr)-2)+'> ' + self.col_norm_ni
        

class Prompt2:
    """Interactive continuation prompt."""
    def __init__(self,cache,colors='NoColor',prompt='   .%n.:'):
        self.cache = cache
        self.color_table = PromptColors
        self.color_table.set_active_scheme(colors)
        Colors = self.color_table.active_colors # shorthand
        self.col_p2 = Colors.in_prompt2
        self.col_norm = Colors.normal
        self.p_template = prompt + ' '

    def __str__(self):
        ndots = len(`self.cache.prompt_count`)
        curr = self.p_template.replace('%n','.'*ndots)
        return self.col_p2 + curr + self.col_norm

#-----------------------------------------------------------------------------
class CachedOutput:
    """Class for printing output from calculations while keeping a cache of
    reults. It dynamically creates global variables prefixed with _ which
    contain these results.

    Meant to be used as a sys.displayhook replacement, providing numbered
    prompts and cache services.

    Initialize with initial and final values for cache counter (this defines
    the maximum size of the cache."""

    def __init__(self,cache_size,Pprint,colors='NoColor',input_sep='\n',
                 output_sep='\n',output_sep2='',user_ns={},
                 ps1 = None, ps2 = None,ps_out = None,
                 input_hist = None):

        self.color_table = PromptColors
        cache_size_min = 20
        if cache_size <= 0:
            self.do_full_cache = 0
            cache_size = 0
        elif cache_size < cache_size_min:
            self.do_full_cache = 0
            cache_size = 0
            warn('caching was disabled (min value for cache size is %s).' %
                 cache_size_min,level=3)
        else:
            self.do_full_cache = 1
            
        self.cache_size = cache_size
        self.input_sep = input_sep

        # Set input prompt strings and colors
        if cache_size == 0:
            if ps1.find('%n') > -1: ps1 = '>>> '
            if ps2.find('%n') > -1: ps2 = '>>> '
        self.ps1_str = self._set_prompt_str(ps1,'In [%n]:','>>> ')
        self.ps2_str = self._set_prompt_str(ps2,'   .%n.:','... ')
        self.set_colors(colors)

        # Set output string as an Itpl object (evaluates dynamically)
        ps_out = self._set_prompt_str(ps_out,'Out[%n]:','') + ' '
        self.ps_out_str = Itpl('${self.col_op}'+
                               ps_out.replace('%n','$self.col_num'
                                             '$self.prompt_count'
                                             '$self.col_op') + \
                               '$self.col_norm')
        
        # other more normal stuff
        # b/c each call to the In[] prompt raises it by 1, even the first.
        self.prompt_count = 0
        self.cache_count = 1
        self.entries = [None]  # output counter starts at 1 for the user
        self.Pprint = Pprint
        self.output_sep = output_sep
        self.output_sep2 = output_sep2
        self._,self.__,self.___ = '','',''
        self.pprint_types = map(type,[(),[],{}])
        
        # we need a reference to the user-level namespace
        self.user_ns = user_ns
        # and to the user's input
        self.input_hist = input_hist
        # these are deliberately global:
        to_user_ns = {'_':self._,'__':self.__,'___':self.___}
        self.user_ns.update(to_user_ns)

    def _set_prompt_str(self,p_str,cache_def,no_cache_def):
        if p_str:
            return p_str
        else:
            if self.do_full_cache:
                return cache_def
            else:
                return no_cache_def
                
    def set_colors(self,colors):
        # The Prompt1/2 stuff seems ugly, and I'm not sure how clean it
        # actually is deep down.  but it works, so fo now it stays!
        self.color_table.set_active_scheme(colors)
        Colors = self.color_table.active_colors # shorthand
        if self.do_full_cache:
            self.prompt1 = Prompt1(self,colors=colors,input_sep = self.input_sep,
                                   prompt = self.ps1_str)
            self.prompt2 = Prompt2(self,colors=colors,prompt = self.ps2_str)
            self.col_op = Colors.out_prompt
            self.col_num = Colors.out_number
            self.col_norm = Colors.normal
        else:
            self.prompt1 = self.input_sep + Colors.in_prompt + self.ps1_str + \
                           Colors.normal
            self.prompt2 = Colors.in_prompt2 + self.ps2_str + Colors.normal

    def __call__(self,arg=None):
        """Printing with history cache management.
        
        This is invoked everytime the interpreter needs to print, and is activated
        by setting the variable sys.displayhook to it."""

        if arg is not None:
            # first handle the cache and counters
            self.update(arg)
            # do not print output if input ends in ';'
            if self.input_hist[self.prompt_count].endswith(';\n'):
                return

            Term.out.write(self.output_sep)  # don't use print, puts an extra space
            if self.do_full_cache:
                Term.out.write(str(self.ps_out_str))

            if isinstance(arg,Macro):
                print 'Executing Macro...'
                Term.out.flush()  # in case the macro takes a long time to execute
                exec arg.value in self.user_ns
                return None

            # and now call a possibly user-defined print mechanism
            self.display(arg)
            
            Term.out.write(self.output_sep2)
            Term.out.flush()


    def _display(self,arg):
        """Default printer method, uses pprint.

        This can be over-ridden by the users to implement special formatting
        of certain types of output."""

        if self.Pprint:
            # The following is an UGLY kludge, b/c python fails to properly
            # identify instances of classes imported in the user namespace
            # (they have different memory locations, I guess). Structs are
            # essentially dicts but pprint doesn't know what to do with them.
            try:
                if arg.__class__.__module__ == 'Struct' and \
                   arg.__class__.__name__ == 'Struct':
                    out = 'Struct:\n%s' % pformat(arg.dict())
                else:
                    out = pformat(arg)
            except:
                out = pformat(arg)
            if '\n' in out:
                print
            print >>Term.out, out
        else:
            print >>Term.out, arg

    # Assign the default display method:
    display = _display

    def update(self,arg):
        #print '***cache_count', self.cache_count # dbg
        if self.cache_count >= self.cache_size and self.do_full_cache:
            self.flush()
        self.___ = self.__
        self.__ = self._
        self._ = arg
        # hackish access to top-level  namespace to create _1,_2... dynamically
        to_main = {'_':self._,'__':self.__,'___':self.___}
        if self.do_full_cache:
            self.cache_count += 1
            self.entries.append(arg)
            new_result = '_'+`self.prompt_count`
            to_main[new_result] = self.entries[-1]
        self.user_ns.update(to_main)
        self.user_ns['_oh'][self.prompt_count] = arg

    def flush(self):
        if not self.do_full_cache:
            raise ValueError,"You shouldn't have reached the cache flush "\
                  "if full caching is not enabled!"
        warn('Output cache limit (currently '+\
              `self.cache_count`+' entries) hit.\n'
             'Flushing cache and resetting history counter...\n'
             'The only history variables available will be _,__,___ and _1\n'
             'with the current result.')
        # delete auto-generated vars from global namespace
        for n in range(1,self.prompt_count + 1):
            key = '_'+`n`
            try:
                del self.user_ns[key]
            except: pass
        self.prompt_count = 1
        self.cache_count = 1
        
