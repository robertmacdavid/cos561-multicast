#!/bin/bash

# Note: Mininet must be run as root.  So invoke this shell script
# using sudo.

nodecount=4


sudo killall controller
sudo fuser -k 6633/tcp
sudo mn -c

echo -----------------------------------------
echo ---------------Cleanup Done--------------
echo -----------------------------------------

    
python topo_creator.py --node-count $nodecount
