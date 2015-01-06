"""Custom topology example
    Two directly connected switches plus a host for each switch:
    host --- switch --- switch --- host
    Adding the 'topos' dict with a key/value pair to generate our newly defined
    topology enables one to pass in '--topo=mytopo' from the command line.
    """

from mininet.topo import Topo

dummy = "10.255.255.255"

class CycleTopo(Topo):
    "Cycle of switches with two hosts per switch."
    def build(self, n=4):
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
        
        dummyHost = self.addHost('hd', ip=dummy)
        # connect it to an arbitrary switch
        self.addLink(dummyHost, switchList[0])


topos = { 'cycletopo': ( lambda x=4: CycleTopo(x) ) }