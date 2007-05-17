# This is a batch script for the LoadLeveler batch system on bassi and seaborg.
# To start up the IPython controller and engine do the following
# 1.  On a head node (b0301 for this example), start the controller using
# b0301> (ipcontroller -l controller &)
# 2.  Modify this script appropriately and submit it using:
# b0301> llsubmit ipengine-ll.bat
# 3.  Check the log files to see if things look OK.
# 4.  Connect to the controller from IPython.

#@ job_name        = ipengine
#@ account_no      = incite7
#@ output          = ipengine.out
#@ error           = ipengine.err
#@ job_type        = parallel
#@ environment     = COPY_ALL
#@ notification    = complete
#@ network.MPI     = sn_all,not_shared,us
#@ node_usage      = not_shared
#@ class           = interactive
#@ bulkxfer        = yes
#
#
#@ tasks_per_node  = 8
#@ node            = 4
#@ wall_clock_limit= 00:15:00
#
#@ queue

ppython $HOME/usr/local/bin/ipengine -l engine --controller-ip=b0301.nersc.gov
