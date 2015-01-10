#!/usr/bin/python
    
from mininet.topo import Topo
from mininet.net import Mininet
from mininet.log import setLogLevel
from mininet.cli import CLI
from mininet.node import Controller, RemoteController

import math

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


class TreeTopo(Topo):
    "A tree of switches with one host per switch."
    # n means how many levels in the tree, d means the how may children each switch has
    def build(self, n=3, d=2):
      for level in range(n):
        num_switches = int(math.pow(d,level))
        total_switches = (int(math.pow(d,level))-1)/(d-1)
        switchList = self.switches(sort=True)
        print switchList
        for i in range(total_switches, num_switches + total_switches):
          print "adding switch %d at level %d" %(i+1, level)
          switch = self.addSwitch('s%s' %(i+1))
          host = self.addHost('h%s' %(i+1), defaultRoute="via %s" %dummy)
          self.addLink(switch, host)

          if level > 0:
            last_level_start = (int(math.pow(d,level-1))-1)/(d-1)
            index = (i - total_switches)/d + last_level_start  # go to the start of the last level and advance
            parent = switchList[index]
            self.addLink(parent, switch)
        
      # hack to make hosts send unknown packets through their switches
      # this dummy host will be everyone's default gateway
      dummyHost = self.addHost('hd', ip=dummy)
      # connect it to an arbitrary switch
      self.addLink(dummyHost, switchList[0])



def simpleTest():
    "Create and test a simple network"
    
    # the topo must be passed in like so
    # you cannot do   topo = CycleTopo()
    #                 net = Mininet(topo=topo,...)
    # this causes wild issues. it must be like mininet(topo())
    #topo = CycleTopo(n=3)
    topo = TreeTopo(n=3,d=2)
    net = Mininet(topo=topo,
                  controller=RemoteController('c0', ip='127.0.0.1', port=6633))

    #net = Mininet(topo=CycleTopo(n=3),
     #             controller=RemoteController('c0', ip='127.0.0.1', port=6633))
    
    net.start()
    print "Terminal Open"
    h = []  # list of hosts
    s = []  # list of switches 
    for i in range(len(net.hosts)):
      h.append(net.hosts[i])
    for i in range(len(net.switches)):
      s.append(net.switches[i])

    #net.stop()
    #return
    print s[0].cmd('wireshark &')                       # start wireshark on switch 1, cause host 1 will be group owner
    print s[0].cmd('sleep 10')                          # during this time, go to the wireshark and select every link on switch and start monitoring
    print h[0].cmd('python mc.py create')               # h1 create group
    print h[1].cmd('python mc.py join 255.0.0.1')       # h2 join group 0 (or groupID that is created)
    print h[2].cmd('python mc.py join 255.0.0.1')       # h3 join the same group
    print h[3].cmd('python mc.py join 255.0.0.1')       # h4 join the same group
    print h[1].cmd('python mc.py leave 255.0.0.1')      # h2 leave the group
    print h[0].cmd('python mc.py msg 255.0.0.1')        # h1 sends message to the group
    print h[0].cmd('python mc.py destroy 255.0.0.1')    # h1 close the group
    
    # now, exhaustive test, procedure
    # one host creates group, all other hosts join
    # then host send msg, timeout, all others leave
    # in the end host close group, do this for every host
    for i in range(len(net.hosts)):
      print h[i].cmd('python mc.py create')               # create group
      for j in range(len(net.hosts)):
        if not j == i:
          print h[j].cmd('python mc.py join 255.0.0.1')   # all others join
      print h[i].cmd('python mc.py msg 255.0.0.1')        # sends msg
      for j in range(len(net.hosts)):
        if not j == i:
          print h[j].cmd('python mc.py leave 255.0.0.1')  # all others leave
      print h[i].cmd('python mc.py destroy 255.0.0.1')    # close group

    CLI(net) 
    # this is the terminal for interactions
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