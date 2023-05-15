#include <string>
#include "ns3/object.h"

#ifndef SPECIE_H
#define SPECIE_H
namespace ns3{

class Specie : public Object{
private:
    /* data */
public:
    std::string str;
    /**
    * \brief Get the type ID.
    * \return the object TypeId
    */
    static TypeId GetTypeId (void);
    Specie();
    template<class T> Specie(T val):str(val){};
    std::string GetName() const;
};
    
}
#endif