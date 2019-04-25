# dockernet

- Overview

1) Dockernet is CLI based tool. 
2) It leverages ‘docker’ containerization platform.
3) It provides efficient and reduced resources testbed to test Opendaylight controller features, stability and performance with large number of virtual OVS switches running inside docker containers with isolation.
4) It will increase productivity many folds for feature development and testing by providing scale environment to test.

- Dockernet features

1) Start/stop switches in docker container
2) Connect switches to ODL for openflow and ovsdb connection
3) Dump flows, flow-count, tables, ports, groups, ovs-show
4) Add tap ports and vm ports to switch
5) Bind tap ports to neutron
6) Create neutron network/subnet/ports
7) Show docker container count and details
8) Datapath testing with Ping among vm ports
9) Cleanup

- Dockernet Help

$ dockernet -h
usage: dockernet [-h]
            [--start-switches NUM_OF_SWITCHES_TO_START]
            [--stop-switches NUM_OF_SWITCHES_TO_STOP]
            [--controller-ip CONTROLLER_IP]
            [--dump <all,flows,flow-count,ports,groups,tables,ovs-show>]
            [--dump-range <START_NUM,END_NUM>]
            [--show-container-count] [--show-containers NUM_OF_CONTAINERS]
            [--add-ports NUM_OF_PORTS_TO_ADD_TO_SWITCH]
            [--bind-ports NUM_OF_PORTS_TO_BIND_TO_NEUTRON]
            [--del-ports NUM_OF_PORTS_TO_DELETE_FROM_SWITCH]
            [--create-network] [--create-subnet] [--del-neutron-data]
            [--output-file]
            [--create-ping-ips-file] [--ping-all]
            [--cleanup]


- Dockernet CLI commands

- dockernet --start-switches 2 --controller-ip '172.17.0.1'
- dockernet --show-container-count
- dockernet --add-ports 2
- dockernet --dump flow-count --range 1,2
- dockernet --dump flows --range 1,2 --output-file
- dockernet --create-network --controller-ip '172.17.0.1'
- dockernet --create-subnet --controller-ip '172.17.0.1'
- dockernet --bind-ports 2 --controller-ip '172.17.0.1'
- dockernet --create-ping-ips-file --range 1,2
- dockernet --ping-all --range 1,2
- dockernet --ping-all --range 1,2 --output-file
- dockernet --cleanup --controller-ip '172.17.0.1'
