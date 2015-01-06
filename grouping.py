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

JOIN_REQUEST = 5566
LEAVE_REQUEST = 6655


class grouping(DynamicPolicy):
   def __init__(self):
      self.last_topology = None
      self.lock = Lock()

      self.group = defaultdict(list)
      join_query = packets(-1, group_by=['srcip'])
      join_query.register_callback(self.join_group)

      leave_query = packets(-1, group_by=['srcip'])
      leave_query.register_callback(self.leave_group)
      self._policy = (match(dstport=JOIN_REQUEST) >> join_query) + (match(dstport=LEAVE_REQUEST) >> leave_query)

   def set_network(self, network):
      with self.lock:
         print '---Edges'
         print '\n'.join(['s%s[%s]---s%s[%s]\ttype=%s' % (s1,data[s1],s2,data[s2],data['type']) for (s1,s2,data) in network.topology.edges(data=True)])
         print network.topology
         print '---Has changed:'

         if self.last_topology:
             print self.last_topology != network.topology
         else:
             print True
         self.last_topology = network.topology
         print network.topology.number_of_nodes()
   def is_in_group(self, owner, client):
     if (owner == client or client in self.group[owner]):
       return True
     else:
       return False

   def join_group(self,pkt):
     if (self.is_in_group(owner = pkt['dstip'], client = pkt['srcip']) == False):
        self.group[pkt['dstip']].append(pkt['srcip'])
        print pkt['srcip'], ' connected to ', pkt['dstip']

   def leave_group(self, pkt):
     if (self.is_in_group(owner = pkt['dstip'], client = pkt['srcip']) == True):
       self.group[pkt['dstip']].remove(pkt['srcip'])
       print pkt['srcip'], ' left ', pkt['dstip']

def main():

   return grouping() + mac_learner()


