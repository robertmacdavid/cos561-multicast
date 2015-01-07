
# some imports
import socket, sys
from struct import *

import logging
logging.getLogger("scapy.runtime").setLevel(logging.ERROR)
from scapy.all import *

# this block gets the host's non-loopback adapter's IPv4 address
from netifaces import AF_INET, AF_INET6, AF_LINK, AF_PACKET, AF_BRIDGE
import netifaces as ni
ifaces = ni.interfaces()
ifaces = [iface for iface in ifaces if iface != "lo"]
host_address = ni.ifaddresses(ifaces[0])[2][0]['addr']

commIP = "255.0.0.0"
protos = {'create':250, 'destroy':251, 'join':252, 'leave':253}


# check input for some correctness
def usage():
    print 'Usage: python %s <Action> <GroupIP>' % (sys.argv[0])
    print 'Actions: create, destroy, join, leave, msg. (create takes no GroupIP)'
    sys.exit()

if len(sys.argv) < 2:
    usage()

if sys.argv[1][0] == 'c':
    if len(sys.argv) != 2:
        usage()
elif len(sys.argv) != 3:
    usage()
# done checking




# send a packet and return the response
def contactControl(host, groupID, protocol):
    p = IP(ttl=3)
    p.src = host
    p.dst = groupID
    p.proto = protocol
    # p.show()
    response = sr1(p, timeout = 2, verbose=0)
    if response == None:
        print "No response received."
        exit()
    return response

# response printing duh
def printResponse(resp):
    print "Got response: Protocol %d, Source %s" %(resp.proto, resp.src)
    # hexdump(resp)
    # uncomment the above line for a hex dump of the response packet



# handle a request to create a group
def create(host, groupID = commIP):
    print "Create a group..."
    resp = contactControl(host, groupID, protos['create'])
    printResponse(resp)


# handle a request to destroy a group
def destroy(host, groupID):
    print "Destroy", groupID, "..."
    resp = contactControl(host, groupID, protos['destroy'])
    printResponse(resp)

# handle a request to join a group
def join(host, groupID):
    print "Join", groupID, "..."
    resp = contactControl(host, groupID, protos['join'])
    printResponse(resp)

# handle a request to leave a group
def leave(host, groupID):
    print "Leave", groupID, "..."
    resp = contactControl(host, groupID, protos['leave'])
    printResponse(resp)




actions = {'c':create, 'd':destroy, 'j':join, 'l':leave}

action = sys.argv[1][0]


# special handling because create takes no groupID
group = commIP
if action != 'c':
    group = sys.argv[2]


# run the desired action
if action != 'm':
    print "Sending request to",
    actions[action](host_address, group)
# handle data messages in a special way cause the payload and no response
else:
    data = raw_input("Type the UDP Payload: ")
    print "Sending data '%s' to" % data, group
    
    send( IP(src=host_address, dst=group)/UDP()/(data) )
                             
                             

"""

"skipping actions"

req = IP(ttl=3)
req.src = sys.argv[2]
req.dst = sys.argv[3]
req.proto = 250
resp = sr1(req, timeout = 3, verbose = 0)
if resp == None:
    print "No response."
    exit()

if resp.proto == 1:
    print "Got an icmp response"
else:
    print "Got non-icmp response"

print "Response source: ", resp.src
"""




