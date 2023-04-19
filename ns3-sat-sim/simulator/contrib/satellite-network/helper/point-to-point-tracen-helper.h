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
 *        Paul
 */
#ifndef POINT_TO_POINT_TRACEN_HELPER_H
#define POINT_TO_POINT_TRACEN_HELPER_H

#include "ns3/object-factory.h"
#include "ns3/net-device-container.h"
#include "ns3/node-container.h"
#include <map>
#include "ns3/point-to-point-tracen-net-device.h"

namespace ns3 {

class NetDevice;
class Node;

/**
 * \brief Build a set of PointToPointTracenNetDevice objects
 * Copied from PointToPointHelper, but TraceUserHelperForDevice functionalities were removed, as I prefer to use
 * personalised traces rather than conventional ones 
 *
 * Normally we eschew multiple inheritance, however, the classes 
 * PcapUserHelperForDevice and AsciiTraceUserHelperForDevice are
 * "mixins".
 */
class PointToPointTracenHelper
{
public:
  /**
   * Create a PointToPointTracenHelper to make life easier when creating point to
   * point networks.
   */
  PointToPointTracenHelper (const std::map<std::string, std::map<std::string, std::string>> node_if_params, const std::map<std::string, std::string> channel_params);
  virtual ~PointToPointTracenHelper () {}

  /**
   * Each point to point net device must have a queue to pass packets through.
   * This method allows one to set the type of the queue that is automatically
   * created when the device is created and attached to a node.
   *
   * \param nodetype the following parameters will depend on the object
   * \param type the type of queue
   * \param n1 the name of the attribute to set on the queue
   * \param v1 the value of the attribute to set on the queue
   * \param n2 the name of the attribute to set on the queue
   * \param v2 the value of the attribute to set on the queue
   * \param n3 the name of the attribute to set on the queue
   * \param v3 the value of the attribute to set on the queue
   * \param n4 the name of the attribute to set on the queue
   * \param v4 the value of the attribute to set on the queue
   *
   * Set the type of queue to create and associated to each
   * PointToPointTracenNetDevice created through PointToPointTracenHelper::Install.
   */
  void
  SetQueue (std::string nodetype, std::string type,
                     std::string n1, const AttributeValue &v1,
                     std::string n2, const AttributeValue &v2,
                     std::string n3, const AttributeValue &v3,
                     std::string n4, const AttributeValue &v4);

  /**
   * Set an attribute value to be propagated to each Channel created by the
   * helper.
   *
   * \param name the name of the attribute to set
   * \param value the value of the attribute to set
   *
   * Set these attribute on each ns3::PointToPointChannel created
   * by PointToPointTracenHelper::Install
   */
  void SetChannelAttribute (std::string name, const AttributeValue &value);

  /**
   * \param c a set of nodes
   * \return a NetDeviceContainer for nodes
   *
   * This method creates a ns3::PointToPointChannel with the
   * attributes configured by PointToPointTracenHelper::SetChannelAttribute,
   * then, for each node in the input container, we create a 
   * ns3::PointToPointTracenNetDevice with the requested attributes, 
   * a queue for this ns3::NetDevice, and associate the resulting 
   * ns3::NetDevice with the ns3::Node and ns3::PointToPointChannel.
   */
  NetDeviceContainer Install (NodeContainer c);

  /**
   * \param a first node
   * \param b second node
   * \return a NetDeviceContainer for nodes
   *
   * Saves you from having to construct a temporary NodeContainer. 
   * Also, if MPI is enabled, for distributed simulations, 
   * appropriate remote point-to-point channels are created.
   */
  NetDeviceContainer Install (Ptr<Node> a, Ptr<Node> b);

  /**
   * \param a first node
   * \param bName name of second node
   * \return a NetDeviceContainer for nodes
   *
   * Saves you from having to construct a temporary NodeContainer.
   */
  NetDeviceContainer Install (Ptr<Node> a, std::string bName);

  /**
   * \param aName Name of first node
   * \param b second node
   * \return a NetDeviceContainer for nodes
   *
   * Saves you from having to construct a temporary NodeContainer.
   */
  NetDeviceContainer Install (std::string aName, Ptr<Node> b);

  /**
   * \param aName Name of first node
   * \param bName name of second node
   * \return a NetDeviceContainer for nodes
   *
   * Saves you from having to construct a temporary NodeContainer.
   */
  NetDeviceContainer Install (std::string aName, std::string bName);

  

  std::map<std::string, ObjectFactory> m_queueFactories;         //!< Queue Factories
  ObjectFactory m_channelFactory;       //!< Channel Factory
  std::map<std::string, ObjectFactory> m_deviceFactories;        //!< Device Factory
#ifdef NS3_MPI
  ObjectFactory m_remoteChannelFactory; //!< Remote Channel Factory
#endif

private:
  void SetDevParam(Ptr<PointToPointTracenNetDevice> dev, const std::string& nodetype);
  std::map<std::string, std::map<std::string, std::string>> m_node_if_params;
};

} // namespace ns3

#endif /* POINT_TO_POINT_HELPER_H */
