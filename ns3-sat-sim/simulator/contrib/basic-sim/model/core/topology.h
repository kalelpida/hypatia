#ifndef TOPOLOGY_H
#define TOPOLOGY_H

#include "ns3/core-module.h"
#include "ns3/node-container.h"
#include "ns3/inet-socket-address.h"

namespace ns3 {

class Topology : public Object
{
public:
    static TypeId GetTypeId (void);
    virtual const NodeContainer& GetNodes() = 0;
    virtual int64_t GetNumNodes() = 0;
    virtual bool IsValidEndpoint(int64_t node_id) = 0;
    virtual const std::set<int64_t>& GetEndpoints() = 0;
    virtual void RegisterFlow(std::pair<InetSocketAddress,InetSocketAddress> quadruplet, uint64_t flowId)=0;//from a source(Adress, port)-dest(Address) to a flow index
};

}

#endif //TOPOLOGY_H
