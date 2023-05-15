
#include "ns3/traffic-control-helper.h"
#include "ns3/string.h"
#include "ns3/data-rate.h"
#include "ns3/rr-queue-disc.h"

#include "device-factory-helper.h"
namespace ns3 {
    
void setQdiscParams(QueueDiscContainer& qdc, const std::map<std::string, std::string> paramap){
    // Aggregate NetDeviceQueueInterface objects to connect
    // the device queue to the interface (used by traffic control layer
    for (const auto&  pair : paramap){
    if (pair.first=="ChildQueueDisc"){
        continue;//should already be done
    }
    std::string avant, suite(pair.second);
    size_t i=suite.find(' ');
    if (i==std::string::npos){
        continue; // This is not a tc queue parameter
    }
    avant = suite.substr(0, i);
    suite = suite.substr(i+1);
    if ( avant ==  "QueueSize" ){
        if (pair.first.rfind("Child", 0) == 0) { // pos=0 limits the search to the prefix
        // s starts with prefix
        //child queue factory, for RRQueue
            qdc.Get(0)->GetObject<RRQueueDisc>()->GetChildQueueFactory().Set(pair.first.substr(5), QueueSizeValue(QueueSize(suite)));
        } else{
            qdc.Get(0)->SetAttribute(pair.first, QueueSizeValue(QueueSize(suite)));
        }
    } else if ( avant == "String"){
        if (pair.first.rfind("Child", 0) == 0) {
            qdc.Get(0)->GetObject<RRQueueDisc>()->GetChildQueueFactory().Set(pair.first.substr(5),  StringValue(suite));
        } else{
            qdc.Get(0)->SetAttribute(pair.first,  StringValue(suite));
        }
    } else if ( avant == "DataRate"){
        if (pair.first.rfind("Child", 0) == 0) {
            qdc.Get(0)->GetObject<RRQueueDisc>()->GetChildQueueFactory().Set(pair.first.substr(5),  DataRateValue(DataRate(suite)));
        } else{
            qdc.Get(0)->SetAttribute(pair.first,  DataRateValue(DataRate(suite)));
        }
    } else if ( avant == "Uinteger"){
        if (pair.first.rfind("Child", 0) == 0) {
            qdc.Get(0)->GetObject<RRQueueDisc>()->GetChildQueueFactory().Set(pair.first.substr(5),  UintegerValue(std::stoul(suite)));
        } else{
            qdc.Get(0)->SetAttribute(pair.first,  UintegerValue(std::stoul(suite)));
        }
    } else {
        NS_ABORT_MSG("Soucis avec attribut " << pair.first << " type non reconnu");
    }
    }
}

void setObjFactoryParams(ObjectFactory& objfactory, const std::map<std::string, std::string> paramap){
    for (const auto&  pair : paramap){
        std::string avant, suite(pair.second);
        size_t i=suite.find('~');
        if (i==std::string::npos){
            continue; // This is not a tc queue parameter
        }
        avant = suite.substr(0, i);
        suite = suite.substr(i+1);
        if ( avant ==  "DataRate" ){
            objfactory.Set(pair.first,  DataRateValue(DataRate(suite)));
        } else if ( avant == "String"){
            objfactory.Set(pair.first,  StringValue(suite));
        } else if ( avant == "Uinteger"){
            objfactory.Set(pair.first,  UintegerValue(std::stoul(suite)));
        } else if ( avant == "Time"){
            objfactory.Set(pair.first, TimeValue(Time(suite)));
        } else {
            NS_ABORT_MSG("Soucis avec attribut " << pair.first << " type non reconnu");
        }
    }
}

}// namespace