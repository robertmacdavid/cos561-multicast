#!/usr/bin/python
    
from mininet.topo import Topo
from mininet.net import Mininet
from mininet.log import setLogLevel
from mininet.cli import CLI
from mininet.node import Controller, RemoteController

dummy = "10.0.0.255"

class CycleTopo(Topo):
    "Cycle of switches with two hosts per switch."
    def build(self, n=3):
        # build the cycle nodes
        for i in range(n):
            switch = self.addSwitch('s%s' % (i + 1))
            host1 = self.addHost('h%s' % (2*i + 1), defaultRoute="via %s" %dummy)
            host2 = self.addHost('h%s' % (2*i + 2), defaultRoute="via %s" %dummy)
            self.addLink(host1, switch)
            self.addLink(host2, switch)
        
        # connect the cycle
        switchList = self.switches(sort=True)
        
        for i in range(len(switchList)):
            self.addLink(switchList[i-1], switchList[i])
        
        
        # hack to make hosts send unknown packets through their switches
        # this dummy host will be everyone's default gateway
        dummyHost = self.addHost('hd', ip=dummy)
        # connect it to an arbitrary switch
        self.addLink(dummyHost, switchList[0])


topos = { 'cycletopo': ( lambda x=4: CycleTopo(x) ) }


def simpleTest():
    "Create and test a simple network"
    
    # the topo must be passed in like so
    # you cannot do   topo = CycleTopo()
    #                 net = Mininet(topo=topo,...)
    # this causes wild issues. it must be like mininet(topo())
    net = Mininet(topo=CycleTopo(n=3),
                  controller=RemoteController('c0', ip='127.0.0.1', port=6633))
    
    net.start()
    print "Terminal Open"
    CLI(net) # this is the terminal for interactions
    # you can run experiments before and/or after the terminal whatever
    # do stuff like try different topos and build large groups automatically
    # you can use mc.py by doing node.cmd('commandline input')
    # or node.sendCmd('commandline input')
    # look up all the mininet example scripts and the tutorial
    print "Stopping network"
    net.stop()
    
if __name__ == '__main__':
    # Tell mininet to print useful information
    setLogLevel('info')
    simpleTest()