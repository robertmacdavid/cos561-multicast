#!/bin/bash

# Note: Mininet must be run as root.  So invoke this shell script
# using sudo.


nodecount=4

sudo mn --custom ./custom_topo.py --topo=cycletopo,$nodecount --controller remote --mac




