#- The names of the copyright holds and contributors may not be used to       #
#   endorse or promote products derived from this work without specific        #
#   prior written permission.                                                  #
#                                                                              #
# Unless required by applicable law or agreed to in writing, software          #
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT    #
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the     #
# LICENSE file distributed with this work for specific language governing      #
# permissions and limitations under the License.                               #
################################################################################
import collections

from pyretic.lib.corelib import *
from pyretic.lib.std import *
from collections import defaultdict
from pyretic.lib.query import *
from multiprocessing import Lock
import steiner_tree as st

from pyretic.modules.mac_learner import mac_learner
import os

CREATE_CODE = 250
JOIN_CODE = 252
LEAVE_CODE = 253
CLOSE_CODE = 251

MAX_GROUP_NUM = 256

MULTICAST_MASK = IPPrefix('255.0.0.0/8')
error_address = "0.0.0.0"

NO_OWNER = -1

#group id is always incoded in dest ip
def get_group_id(pkt):
   return int(pkt['dstip'].__repr__().split('.')[3])

def group_ip(n):
   string_ip = "255.0.0." + str(n)
   return IPAddr(string_ip)

TODO = -1
UNKNOWN = -1
class Home:
   def __init__(self):
      self.switch = UNKNOWN
      self.mac = UNKNOWN
      self.port = UNKNOWN



def multicast_reply(network, pkt, groupID):

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
   rp = rp.modify(srcip=group_ip(groupID))
   rp = rp.modify(srcmac=dstmac)

   rp = rp.modify(dstip=srcip)
   rp = rp.modify(dstmac=srcmac)

   rp = rp.modify(raw='')

   network.inject_packet(rp)





def make_tree(topo, voi):
   if len(voi) < 2:
      return None

   self = Topology(st.make_steiner_tree(topo, voi))
   self.copy_attributes(topo)
   self.reconcile_attributes(topo)

   return self

class MulticastTree():
   def __init__(self, tree_constructor = make_tree):
      self.voi = []
      self.voi_user_count = defaultdict(int)
      self.topo = None
      self.tree = None
      self.switches_with_ports = None
      self.tree_constructor = tree_constructor

   def update_tree(self):
      print self.voi
      if self.topo != None:
         updated_tree = self.tree_constructor(self.topo, self.voi)
         if updated_tree != self.tree:
            self.tree = updated_tree
         if (not self.is_none()):
            self.switches_with_ports = [(switch, [port for port in attrs['ports'].keys() if self.topo.node[switch]['ports'][port].linked_to is not None])
                                  for switch, attrs in self.tree.nodes(data=True)]


   def add_voi(self, new_voi):
      if (not new_voi in self.voi):
         self.voi.append(new_voi)
         self.update_tree()

      self.voi_user_count[new_voi] = self.voi_user_count[new_voi] + 1

   def remove_voi(self, bad_voi):
      if (bad_voi in self.voi):
         self.voi_user_count[bad_voi] = self.voi_user_count[bad_voi] - 1
         if (self.voi_user_count[bad_voi] == 0):
            self.voi.remove(bad_voi)
            self.update_tree()

   def clear(self):
      self.voi = []
      self.update_tree()

   def get_tree(self):
      return self.tree

   def is_none(self):
      return self.tree.__class__.__name__ == "NoneType"

   def get_tree_policy(self):
      if (self.is_none()):
         return drop
      print self.switches_with_ports

      return parallel([match(switch=switch) >>
             parallel(map(xfwd, ports))
             for switch,ports
               in self.switches_with_ports])
            #   in [(switch,attrs['ports'].keys())
            #                      for switch,attrs in self.tree.nodes(data=True)]])

   def topo_change(self, topology):
 #     print "topo changed"
#      print topology 
      self.topo = topology
      self.update_tree()

group_owner = [NO_OWNER for i in range(MAX_GROUP_NUM)]
group_members = [[]] * MAX_GROUP_NUM
group_tree = [MulticastTree() for i in range(MAX_GROUP_NUM)]
host_home = defaultdict(Home)

def is_free_group(group_id):
    return group_owner[group_id] == NO_OWNER

def is_in_group(group_id, client):
    return (client in group_members[group_id])



class MulticastGroup(DynamicPolicy):
    def __init__(self, my_id):
        super(MulticastGroup, self).__init__()
        self.my_id = my_id
        self.policy = drop
	self.topo = None
    def update_policy(self):
        #print "Updating rules for ", self.my_id
        tree = group_tree[self.my_id]
        if not is_free_group(self.my_id):
            local_policy = drop
            for host_ip in group_members[self.my_id]:
                  switch = host_home[host_ip].switch
                  mac = host_home[host_ip].mac
                  port = host_home[host_ip].port
                  print "setting up ", switch, " to forward ", group_ip(self.my_id), " to ", port, " with ", mac
                  local_policy = local_policy + (match(switch=switch) >> modify(dstmac=mac) >> modify(dstip=host_ip) >> fwd(port))

            global_policy = drop
            if not tree.is_none():
               global_policy = tree.get_tree_policy()
            self.policy = match(dstip=group_ip(self.my_id)) >> (global_policy + local_policy)
   
    def set_network(self, network):
       self.topo = network.topology
       group_tree[self.my_id].topo_change(self.topo)
       self.update_policy() 

class Multicast(DynamicPolicy):
    def __init__(self, multicast_group_list):
      super(Multicast, self).__init__()
      self.lock = Lock()
      self.groups = multicast_group_list

      #################################################
      #set up policies for group requests             #
      #################################################
      #packets() sends all the packets to the controller
      leave_query = packets()
      join_query = packets()
      create_query = packets()
      close_query = packets()

      #register callback determines what happens at the controller
      join_query.register_callback(self.join_group)
      #protocol determines which query it is
      self.grouping_policy = (match(protocol=JOIN_CODE)) >> join_query

      leave_query.register_callback(self.leave_group)
      self.grouping_policy = self.grouping_policy + (match(protocol=LEAVE_CODE) >> leave_query)

      create_query.register_callback(self.create_group)
      self.grouping_policy = self.grouping_policy + (match(protocol=CREATE_CODE) >> create_query)

      close_query.register_callback(self.close_group)
      self.grouping_policy = self.grouping_policy + (match(protocol=CLOSE_CODE) >> close_query)


      ###############################################
      #policies for learning host information       #
      ###############################################
      home_learner = packets()
      home_learner.register_callback(self.learn_home_ip)
      self.learning_policy = home_learner

      ###############################################
      #routing policies for IP multicast            #
      ###############################################
      self.control_policy = self.learning_policy + self.grouping_policy
      self.control_filter = match(protocol=CLOSE_CODE) | match(protocol=CREATE_CODE) | match(protocol=LEAVE_CODE) | match(protocol=JOIN_CODE)
      self.policy = self.control_filter >> self.control_policy
      self.network = None
    
    def set_network(self, network):
      if not network is None:
         if (network != self.network):
             self.network = network


    def learn_home_ip(self, pkt):
      if (host_home[pkt['srcip']].switch != pkt['switch'] or host_home[pkt['srcip']].mac != pkt['srcmac']):
         host_home[pkt['srcip']].switch = pkt['switch']
         host_home[pkt['srcip']].mac = pkt['srcmac']
         host_home[pkt['srcip']].port = pkt['inport']
         print "new home of ", pkt['srcip'], ", it's switch ", pkt['switch'], " mac ", pkt['srcmac']

    def join_group(self,pkt):
      print "in join group"
      group_id = get_group_id(pkt)
      self.learn_home_ip(pkt)
      if (is_free_group(group_id)):
         print "trying to join nonexisting group"
         #todo: send an error packet
         multicast_reply(self.network, pkt, error_address)
      else:
         if (group_owner[group_id] == pkt['srcip']):
            print "trying to join your own group"
            #send error packet
            multicast_reply(self.network, pkt, error_address)
            return

         if (is_in_group(group_id = group_id, client = pkt['srcip']) == True):
            print pkt['srcip'], ' trying to reconnect to ', group_id
            #todo: send confirmation packet
            multicast_reply(self.network, pkt, group_id)
            return

         group_members[group_id].append(pkt['srcip'])
         print pkt['srcip'], ' connected to ', group_id
         group_tree[group_id].add_voi(pkt['switch'])
         self.groups[group_id].update_policy()
         #todo: send confirmation packethhhhhhhhhh
         multicast_reply(self.network, pkt, group_id)


    def leave_group(self, pkt):
      print "in leave group"
      group_id = get_group_id(pkt)
      if (is_free_group(group_id)):
         print "trying to leave nonexisting group"
         #todo: send an error packet
         multicast_reply(self.network, pkt, error_address)
      else:
         if (is_in_group(group_id = group_id, client = pkt['srcip']) == True):
            group_members[group_id].remove(pkt['srcip'])
            print pkt['srcip'], ' left ', group_id
            group_tree[group_id].remove_voi(pkt['switch'])
            self.groups[group_id].update_policy()
            #todo: send confirmation packet
            multicast_reply(self.network, pkt, group_id)
         else:
            print "trying to leave not mine group"
            #todo: send error packet
            multicast_reply(self.network, pkt, error_address)

    def create_group(self, pkt):
        with self.lock:
          print "enter create group"

          for i in range(1, MAX_GROUP_NUM):
             checked_group = i
             if is_free_group(checked_group):
                group_owner[checked_group] = pkt['srcip']
                print "group ", checked_group, " created at switch ", pkt['switch'], " ", pkt['ethtype']
                group_tree[checked_group].add_voi(pkt['switch'])
                self.groups[checked_group].update_policy()
                multicast_reply(self.network, pkt, checked_group)
                return

          #todo: send failure packet
          multicast_reply(self.network, pkt, error_address)

    def close_group(self, pkt):
      print "enter close group"
      group_id = get_group_id(pkt)
      if (group_owner[group_id] != pkt['srcip']):
         print "trying to close others group"
         #todo: send failure packet
         multicast_reply(self.network, pkt, error_address)
      else:
         group_members[group_id] = []
         group_owner[group_id] = NO_OWNER
         print "group ", group_id, " closed"
         group_tree[group_id].clear()
         self.groups[group_id].update_policy()
         #todo: send confirm packet
         multicast_reply(self.network, pkt, group_id)

class Printer(DynamicPolicy):
    def __init__(self):
      super(Printer, self).__init__()
      Q = packets()
      Q.register_callback(self.printer)
      self.policy = Q

    def printer(self, pkt):
       #print pkt['switch'], " recieved ", pkt
      print "!!", pkt['protocol']

def main():
    groups = [MulticastGroup(i) for i in range(MAX_GROUP_NUM)]
    our_policy = Multicast(groups) + parallel(groups)
    return if_(match(dstip=MULTICAST_MASK) , our_policy, mac_learner())


