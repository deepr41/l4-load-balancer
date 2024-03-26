# L4 Load balancer

This project is currently work in progress. And will be completed by April 2nd week.

# See the design
Files under /drawings can be viewed in excalidraw.

# What are we doing
We are creating a load balancer which can automatically adapt to an autoscale event.

Approch 1: IaaS approach
In this method we are leveraging the the provider VM we create for every VPC, to also handle the load balancing. When a loadbalancing event occurs, we modify the iptables to refelect the new forwarding rules with the necessary weightage. In effect we are achieving a Weighted Round Robin load balancing.

Apprach 2: VM as a load balancer
In this approach we create a vm which is connected to the same subnet as the servers. We are using iptables to set the forwarding rules to create a weighted round robin load balancing.

