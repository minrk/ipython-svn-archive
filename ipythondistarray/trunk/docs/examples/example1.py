import ipythondistarray as ipda

# Default is block row distributed
# Here, the processor grid shape is picked automatically
a = ipda.DistArray((100,100))
a.plot_dist_matrix()


