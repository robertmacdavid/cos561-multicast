# some imports
import socket, sys
from struct import *

## this shuts up scapy whining about IPv6 errors
import logging
logging.getLogger("scapy.runtime").setLevel(logging.ERROR)
from scapy.all import *
##

## this block gets the host's non-loopback adapter's IPv4 address
from netifaces import AF_INET, AF_INET6, AF_LINK, AF_PACKET, AF_BRIDGE
import netifaces as ni
ifaces = ni.interfaces()
ifaces = [iface for iface in ifaces if iface != "lo"]
host_iface = ifaces[0]
host_address = ni.ifaddresses(host_iface)[2][0]['addr']
##

## GLOBAL VARS HERE ##
commIP = "255.0.0.0"
protos = {'create':250, 'destroy':251, 'join':252, 'leave':253}
protosInverse = {protos[name]:name for name in protos}
failureIP = "0.0.0.0"
######################


## check input for some correctness
def usage():
    print 'Usage: python %s <Action> <GroupIP>' % (sys.argv[0])
    print 'Actions: create, destroy, join, leave, msg, sniff. (create/sniff takes no GroupIP)'
    sys.exit()

if len(sys.argv) < 2:
    usage()

if sys.argv[1][0] == 'c' or sys.argv[1][0] == 's':
    if len(sys.argv) != 2:
        usage()
elif len(sys.argv) != 3:
    usage()
## done checking



def printResponses(resps):
    if len(resps) == 0:
        print "No responses to list."
        exit()
    print "--List of incoming packets--"
    for resp in resps:
        #print "Source: %s, Dest %s, Protocol %d" %(resp[1].src, resp[1].dst, resp[1].proto)
        summaryMod(resp)
    #print resp.summary()
    print "----------------------------"





## send a packet and return the response
def contactControl(host, groupID, protocol):
    p = IP()/UDP()
    p.src = host
    p.dst = groupID
    p.proto = protocol
    # p.show()
    #response = sr1(p, timeout = 2, verbose=0)
    #if response == None:
    #    print "No response received."
    #    exit()
    #return response
    send(p, verbose = 0)
    packets = sniff(filter = "ip", iface = host_iface, timeout = 1)
    printResponses(packets)
    return packets
##


## response printing duh
def printResponse(resp):
    print "Got response: Protocol %d, Source %s" %(resp.proto, resp.src)
    # hexdump(resp)
    # uncomment the above line for a hex dump of the response packet
##


##### Option Functions ######

## handle a request to create a group
def create(host, groupID = commIP):
    print "Create a group..."
    resps = contactControl(host, groupID, protos['create'])
##

## handle a request to destroy a group
def destroy(host, groupID):
    print "Destroy", groupID, "..."
    resps = contactControl(host, groupID, protos['destroy'])
##

## handle a request to join a group
def join(host, groupID):
    print "Join", groupID, "..."
    resps = contactControl(host, groupID, protos['join'])
    group = failureIP
    for resp in resps:
        if resp.dst[:3] == "255":
            group = resp.dst
    if group != failureIP:
        print "Interpreted response as successful join."
        print "---Sniffing %s. Ctrl+C to stop---" % host_iface
        sniff(filter = "ip", iface = host_iface, prn=summaryMod)

## handle a request to leave a group
def leave(host, groupID):
    print "Leave", groupID, "..."
    resps = contactControl(host, groupID, protos['leave'])
##

def sniffy(host, groupID = None):
    print "---Sniffing %s. Ctrl+C to stop---" % host_iface
    sniff(iface = host_iface, prn=summaryMod)
##


def summaryMod(pkt):
    print pkt.summary(),
    if pkt.type != 2048:
        print ''
        return
    proto = pkt.proto
    if proto in protosInverse:
        print "((%s))" % protosInverse[proto].upper()
    else:
        print ''


#############################



## Main Script

actions = {'c':create, 'd':destroy, 'j':join, 'l':leave, 's':sniffy}

action = sys.argv[1][0]


## special handling because create/sniff take no groupID arg
group = commIP
if action != 'c' and action != 's':
    group = sys.argv[2]

# if the given address is short, it must be the group number
# convert it to an IP
if len(group) < 4:
    group = commIP[:8] + group

##


## Run the desired action's function
if action != 'm':
    if action != 's':
        print "Sending request to",
    actions[action](host_address, group)
## Messages to the group are handled differently
else:
    # lets you type the payload so you can recognize it in a packet dump
    #data = raw_input("Type the UDP Payload: ")
    #print "Sending UDP data '%s' to" % data, group
    print "Sending UDP packet to", group
    data = ' '
    
    ## fuzzing the UDP packet fixes some crap with unset header fields
    ## it shouldnt be necessary because SCAPY IS SUPPOSED TO FIX THEM ON SEND
    p = IP(src = host_address, dst = group)/fuzz(UDP()/(data))

    send(p, verbose=0)
    print "Sniffing for responses for 2 seconds.."
    responses = sniff(filter = "ip", iface = host_iface, timeout = 2)
    printResponses(responses)






