#!/usr/bin/python
    
from mininet.topo import Topo
from mininet.net import Mininet
from mininet.util import dumpNodeConnections
from mininet.log import setLogLevel
from mininet.cli import CLI

from argparse import ArgumentParser


parser = ArgumentParser(description="Multicast Topology Creator")
parser.add_argument('--node-count', '-N',
                    type=int,
                    help="Number of nodes in the Topology",
                    default=4)

args = parser.parse_args()

    
class SingleSwitchTopo(Topo):
    "Single switch connected to n hosts."
    def __init__(self, n=4, **opts):
        self.build(n)
    def build(self, n=2):
        switch = self.addSwitch('s1')
        # Python's range(N) generates 0..N-1
        for h in range(n):
            host = self.addHost('h%s' % (h + 1))
            self.addLink(host, switch)


class CycleTopo(Topo):
    "Cycle of switches with two hosts per switch."
    def __init__(self, n=4, **opts):
        self.build(n)
    def build(self, n=4):
        # build the cycle nodes
        for i in range(n):
            switch = self.addSwitch('s%s' % (i + 1))
            host1 = self.addHost('h%s' % (2*i + 1))
            host2 = self.addHost('h%s' % (2*i + 2))
            self.addLink(host1, switch)
            self.addLink(host2, switch)

        # connect the cycle
        switchList = self.switches(sort=True)
        for i in range(len(switchList)):
            self.addLink(switchList[i-1], switchList[i])


def simpleTest():
    "Create and test a simple network"
    topo = CycleTopo(n=args.node_count)
    net = Mininet(topo)
    net.start()
    print "Dumping host connections"
    dumpNodeConnections(net.hosts)
    print "Terminal Open"
    CLI(net)
    print "Stopping network"
    net.stop()
    
if __name__ == '__main__':
    # Tell mininet to print useful information
    setLogLevel('info')
    simpleTest()