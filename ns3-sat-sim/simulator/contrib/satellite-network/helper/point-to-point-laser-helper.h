/* -*- Mode:C++; c-file-style:"gnu"; indent-tabs-mode:nil; -*- */
/*
 * Copyright (c) 2008 INRIA
 *
 * This program is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License version 2 as
 * published by the Free Software Foundation;
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program; if not, write to the Free Software
 * Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
 *
 * Author: Mathieu Lacage <mathieu.lacage@sophia.inria.fr>
 * (based on point-to-point helper)
 * Author: Andre Aguas         March 2020
 *         Simon               2020
 * 
 */


#ifndef POINT_TO_POINT_LASER_HELPER_H
#define POINT_TO_POINT_LASER_HELPER_H

#include "ns3/object-factory.h"
#include "ns3/net-device-container.h"
#include "ns3/node-container.h"
#include "ns3/point-to-point-laser-net-device.h"
#include <map>

namespace ns3 {

class NetDevice;
class Node;

class PointToPointLaserHelper
{
public:

  // Constructors
  PointToPointLaserHelper(const std::map<std::string, std::map<std::string, std::string>> node_if_params);

  // Set point-to-point laser device and channel attributes
  void SetQueue (std::string nodetype, std::string type,
                     std::string n1, const AttributeValue &v1,
                     std::string n2, const AttributeValue &v2,
                     std::string n3, const AttributeValue &v3,
                     std::string n4, const AttributeValue &v4);
  
  void SetChannelAttribute (std::string name, const AttributeValue &value);

  // Installers
  NetDeviceContainer Install (NodeContainer c);
  NetDeviceContainer Install (Ptr<Node> a, Ptr<Node> b);

private:
  ObjectFactory m_channelFactory;       //!< Channel Factory
  ObjectFactory m_remoteChannelFactory; //!< Remote Channel Factory
  std::map<std::string, ObjectFactory> m_queueFactories;         //!< Queue Factories
  std::map<std::string, ObjectFactory> m_deviceFactories;        //!< Device Factory

  std::map<std::string, std::map<std::string, std::string>> m_node_if_params;

  void SetDevParam(Ptr<PointToPointLaserNetDevice> dev, const std::string& nodetype);
};

} // namespace ns3

#endif /* POINT_TO_POINT_LASER_HELPER_H */
