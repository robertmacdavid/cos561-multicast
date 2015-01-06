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

from pyretic.modules.mac_learner import mac_learner
import os

MULTICAST_REQUEST = 5566


class grouping(DynamicPolicy):
   def __init__(self):

     self.group = defaultdict(list)
     Q = packets(99, group_by=['srcip'])     
     Q.register_callback(self.join_group)
     self._policy = match(dstport=MULTICAST_REQUEST) >> Q 

   def is_in_group(self, owner, client):
     if (owner == client or client in self.group[owner]):
       return True
     else:
       return False

   def join_group(self,pkt):
     if (self.is_in_group(owner = pkt['dstip'], client = pkt['srcip']) == False):
	self.group[pkt['dstip']].append(pkt['srcip'])
	print pkt['srcip'], ' connected to ', pkt['dstip']	

def main():

   return grouping() + mac_learner()
 
