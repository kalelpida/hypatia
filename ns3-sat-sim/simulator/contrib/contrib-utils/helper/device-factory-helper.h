
#include "ns3/queue-disc-container.h"
#include "ns3/object.h"
#include "ns3/object-factory.h"
#include <map>


#ifndef DEVFACT_HELPER_H
#define DEVFACT_HELPER_H
namespace ns3 {

void setObjFactoryParams(ObjectFactory& devfactory, const std::map<std::string, std::string> paramap);
void setQdiscParams(QueueDiscContainer& qdc, const std::map<std::string, std::string> paramap);

}
#endif