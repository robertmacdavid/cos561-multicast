import collections

from pyretic.lib.corelib import *
from pyretic.lib.std import *
from pyretic.lib.query import *


def multicast_reply(network, pkt, groupID)
{
    switch = pkt['switch']
    inport = pkt['inport']
    srcip  = pkt['srcip']
    srcmac = pkt['srcmac']
    # dstip  = pkt['dstip']
    dstmac = pkt['dstmac']
    
    

    rp = Packet()
    rp = rp.modify(protocol = 17) # 17 is UDP
    rp = rp.modify(ethtype = 0x0800) # IP type
    rp = rp.modify(switch=switch)
    
    rp = rp.modify(inport=-1)
    rp = rp.modify(outport=inport)
    
    # groupID conveyed through the source IP
    # src and dst MACs are flipped for a response
    rp = rp.modify(srcip=groupID)
    rp = rp.modify(srcmac=dstmac)
    
    rp = rp.modify(dstip=srcip)
    rp = rp.modify(dstmac=srcmac)
    
    rp = rp.modify(raw='')

    network.inject_packet(rp)

}