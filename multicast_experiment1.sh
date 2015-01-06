#!/bin/bash

# Note: Mininet must be run as root.  So invoke this shell script
# using sudo.

nodecount=4


sudo killall controller
sudo fuser -k 6633/tcp
sudo mn -c

echo ------------------------------------------
echo ---------------Cleanup Done---------------
echo ------------------------------------------


pyretic.py pyretic.examples.grouping &

sleep 2

sudo python topo_creator.py --node-count $nodecount

pkill -f pyretic.py

sudo fuser -k 6633/tcp



