#include "specie.h"


namespace ns3 {

TypeId 
Specie::GetTypeId (void)
{
  static TypeId tid = TypeId ("ns3::Specie")
    .SetParent<Object> ()
    .SetGroupName("Network")
    .AddConstructor<Specie> ();
  return tid;
}

Specie::Specie()
{
}

std::string Specie::GetName() const
{
  return str;
}
}