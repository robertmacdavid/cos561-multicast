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

from pyretic.lib.corelib import *
from pyretic.lib.std import *
from collections import defaultdict
from pyretic.lib.query import *
from multiprocessing import Lock

from pyretic.modules.mac_learner import mac_learner
import os

CREATE_CODE = 250
JOIN_CODE = 251
LEAVE_CODE = 252
CLOSE_CODE = 253

MAX_GROUP_NUM = 255

MULTICAST_MASK = IPPrefix('255.0.0.0/8')

NO_OWNER = -1

#dont' know if this wokrs
def send_packet(network, switch, outport, srcip, dstip, dstport):
   rp = Packet()
   rp = rp.modify(switch = switch)
   rp = rp.modify(outport = outport)
   rp = rp.modify(srcip = srcip)
   rp = rp.modify(dstip = dstip)
   rp = rp.modify(dstport = dstport)
   rp = rp.modify(raw='')

   netwrok.inject_packet(rp)

#group id is always incoded in dest ip
def get_group_id(pkt):
   return int(pkt['dstip'].__repr__().split('.')[3])


UNKNOWN = -1
class Home:
   def __init__(self):
      self.switch = UNKNOWN
      self.mac = UNKNOWN

class grouping(DynamicPolicy):
   def __init__(self):
      super(grouping, self).__init__()
      #copied, don't know if we need this line
      self.lock = Lock()

      #keeps trak of taken group IDs
      self.group_owner = [NO_OWNER for i in range(MAX_GROUP_NUM)]
      self.group_members = [[]] * MAX_GROUP_NUM
      #pointer used to chose next free group
      self.curr_group = 0

      #stores all home switches of the given host IP
      self.host_home_switch = defaultdict(Home)

      #packets() sends all the packets to the controller
      leave_query = packets()
      join_query = packets()
      create_query = packets()
      close_query = packets()

      #register callback determines what happens at the controller
      join_query.register_callback(self.join_group)
      #protocol determines which query it is
      self.policy = (match(protocol=JOIN_CODE)) >> join_query

      leave_query.register_callback(self.leave_group)
      self.policy = self.policy + (match(protocol=LEAVE_CODE) >> leave_query)

      create_query.register_callback(self.create_group)
      self.policy = self.policy + (match(protocol=CREATE_CODE) >> create_query)

      close_query.register_callback(self.close_group)
      self.policy = self.policy + (match(protocol=CLOSE_CODE) >> close_query)

      #need this for later tree construction
      home_learner = packets()
      home_learner.register_callback(self.learn_home_ip)
      self.policy = self.policy + home_learner

   def learn_home_ip(self, pkt):
      if (self.host_home_switch[pkt['srcip']].switch != pkt['switch'] or self.host_home_switch[pkt['srcip']].mac != pkt['srcmac']):
         self.host_home_switch[pkt['srcip']].switch = pkt['switch']
         self.host_home_switch[pkt['srcip']].mac= pkt['srcmac']
         print "new home of ", pkt['srcip'], ", it's switch ", pkt['switch'], " mac ", pkt['srcmac']

   def is_free_group(self, group_id):
      return self.group_owner[group_id] == NO_OWNER

   def is_in_group(self, group_id, client):
      return (client in self.group_members[group_id])

   def join_group(self,pkt):
      print "in join group"
      group_id = get_group_id(pkt)
      if (self.is_free_group(group_id)):
         print "trying to join nonexisting group"
         #todo: send an error packet
      else:
         if (self.is_in_group(group_id = group_id, client = pkt['srcip']) == False):
            self.group_members[group_id].append(pkt['srcip'])
            print pkt['srcip'], ' connected to ', group_id
            #todo: change policy
            #todo: send confirmation packet
         else:
            print pkt['srcip'], ' trying to reconnect to ', group_id
            #todo: send confirmation packet

   def leave_group(self, pkt):
      print "in leave group"
      group_id = get_group_id(pkt)
      if (self.is_free_group(group_id)):
         print "trying to leave nonexisting group"
         #todo: send an error packet
      else:
         if (self.is_in_group(group_id = group_id, client = pkt['srcip']) == True):
            self.group_members[group_id].remove(pkt['srcip'])
            print pkt['srcip'], ' left ', group_id
            #todo: change policy
            #todo: send confirmation packet
         else:
            print "trying to leave not mine group"
            #todo: send packet

   def create_group(self, pkt):
      print "enter create group"

      for i in range(MAX_GROUP_NUM):
         checked_group = self.curr_group + i
         if self.is_free_group(checked_group):
            self.group_owner[checked_group] = pkt['srcip']
            print "group ", checked_group, " created at switch ", pkt['switch'], " ", pkt['ethtype']
            #todo: send confirmation packet
            return
   #todo: send failure packet

   def close_group(self, pkt):
      print "enter close group"
      group_id = get_group_id(pkt)
      if (self.group_owner[group_id] != pkt['srcip']):
         print "trying to close others group"
         #todo: send failure packet
      else:
         self.group_members[group_id] = []
         self.group_owner[group_id] = NO_OWNER
         print "group ", group_id, " closed"
         #todo: change policy
         #todo: send confirm packet
def main():

   return if_(match(dstip=MULTICAST_MASK) , grouping(), mac_learner())


