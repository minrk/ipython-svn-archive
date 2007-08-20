from tconfig import TConfigManager,tconf2File

from simpleconf import SimpleConfig


# Make and print to screen the default config
conf = SimpleConfig()
print repr(conf)

# We can save this to disk:
tconf2File(conf,'simple_default.conf',force=True)

# <demo> stop

# The GUI is auto-generated
conf.edit_traits()

# <demo> stop

# A TConfigManager handles the coupling of a TConfig object to a ConfigObj
# file, but the file can even start empty:
fname = 'simple2.conf'
!rm $fname

conf2 = TConfigManager(SimpleConfig,fname)

# This object starts 'empty', meaning it has no changes over the defaults
print conf2

# <demo> stop

# Now make some changes:
conf2.tconf.edit_traits()

# <demo> stop
# And write it out to disk, which only writes the changes
conf2.write()
!cat $fname

# <demo> stop
# You can 'fold' the configurations and write out the whole object as well:
conf2.writeAll()
!cat $fname


# <demo> stop

# Finally, the actual entire Matplotlib configuration:

from mplconfig import MPLConfig
mpc = MPLConfig()
mpc.edit_traits()
