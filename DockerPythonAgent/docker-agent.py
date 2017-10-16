#  Copyright 2017 Quest Inc.
#  ALL RIGHTS RESERVED.
#
#  This file is provided for demonstration and educational uses only.
#  Permission to use, copy, modify and distribute this file for
#  any purpose and without fee is hereby granted, provided that the
#  above copyright notice and this permission notice appear in all
#  copies, and that the name of Dell not be used in
#  advertising or publicity pertaining to this material without
#  the specific, prior written permission of an authorized
#  representative of Quest Inc.
#
#  DELL INC. MAKES NO REPRESENTATIONS OR WARRANTIES ABOUT
#  THE SUITABILITY OF THE SOFTWARE EITHER EXPRESS OR IMPLIED,
#  INCLUDING BUT NOT LIMITED TO THE IMPLIED WARRANTIES OF
#  MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE, OR
#  NON-INFRINGEMENT. DELL SHALL NOT BE LIABLE FOR ANY
#  DAMAGES SUFFERED BY USERS AS A RESULT OF USING, MODIFYING
#  OR DISTRIBUTING THIS OR ITS DERIVATIVES.

"""
A very simple example agent that uses the Docker API for Docker hosts and containers to obtain
and submit inventory and performance information.
"""

# import the standard libraries
import datetime
import traceback
from java.util import ArrayList

# import foglight modules
import foglight.asp
import foglight.logging
import foglight.model
import foglight.utils

# import the modules to collect the data from the specific monitoring target
import docker


# Set up a logger for this Agent.
logger = foglight.logging.get_logger("DockerPythonAgent")

# Get the agent properties
hostname = None
endPoint = None

# A helper class from the foglight.model package that tells us whether an inventory or a
# performance collection is required.
tracker = None


def addToPropertyList(model, propName, item):
    items = model.get_property(propName, ArrayList())
    if not items.contains(item.key):
        items.add(item.key)
        model.set_property(propName, items)


def collect_inventory():
    logger.info("Starting inventory collection")

    update = None
    try:
        update = foglight.topology.begin_update()

        client = docker.DockerClient(base_url=endPoint)
        info = client.info()
        containers = client.containers.list()

        dockerModel = update.create_object("DockerModel", {"name": "DockerModel"})

        dockerHost = update.create_object("DockerHost", {"id": info["ID"]})
        host = update.create_object("Host", {"name": hostname})
        dockerHost.set_property("name", hostname)
        dockerHost.set_property("host", host.key)
        addToPropertyList(dockerModel, "hosts", dockerHost)
        logger.info("A dockerHost topologyobject {0} is created", hostname)

        for container in containers:
            dockerContainer = update.create_object("DockerContainer",
                                                   {"id": container.id,
                                                    "dockerHost": dockerHost.key})
            addToPropertyList(dockerHost, "containers", dockerContainer)
            dockerContainer.set_property("name", container.name)
            logger.info("A dockerContainer topologyobject {0} is created", container.name)

            dockerContainerMemory = update.create_object("DockerContainerMemory",
                                                         {"container": dockerContainer.key})
            dockerContainer.set_property("memory", dockerContainerMemory.key)


        def __inventory_submit_success(key):
            update.commit()
            tracker.record_inventory()
            logger.info("Inventory collection completed and submitted")
            collect_performance()

        update.submit(on_success=__inventory_submit_success)

    except Exception, e:
        logger.error("{0}", traceback.format_exc())
        if update:
            update.abort()


def collect_performance():
    logger.info("Starting performance collection")

    update = foglight.topology.begin_data_collection()

    client = docker.DockerClient(base_url=endPoint)
    info = client.info()
    containers = client.containers.list()

    dockerHost_key = foglight.topology.make_object_key("DockerHost", {"id": info["ID"]})
    # print("dockerHost: ", dockerHost)

    for container in containers:
        dockerContainer_key = foglight.topology.make_object_key("DockerContainer",
                                                                {"id": container.id, "dockerHost": dockerHost_key})
        dockerContainer = update.get_object(dockerContainer_key)
        dockerContainer.set_observation_value("status", container.status)
        logger.info("DockerContainer topologyobject {0} status is set to {1}",
                    dockerContainer["name"], container.status)

        memory_key = foglight.topology.make_object_key("DockerContainerMemory", {"container": dockerContainer_key})
        dockerContainerMemory = update.get_object(memory_key)
        stats = container.stats(stream=False)
        megabyte = 1024*1024
        usage = stats["memory_stats"]["usage"]/megabyte
        max_usage = stats["memory_stats"]["max_usage"]/megabyte
        # print usage
        dockerContainerMemory.set_metric_value("usage", usage)
        dockerContainerMemory.set_metric_value("maxUsage", max_usage)
        logger.info("DockerContainer topologyobject {0} memory usage is set to {1}",
                dockerContainer["name"], usage)

    update.submit()
    tracker.record_performance()
    logger.info("Performance collection completed and submitted")


if __name__ == "__main__":
    try:
        logger.info("Attempting to connect to {0}".format(hostname))

        # Get the agent properties
        hostname = foglight.asp.get_properties().get("host")
        endPoint = foglight.asp.get_properties().get("endPoint")

        # Get the collection frequencies
        frequencies = foglight.asp.get_collector_frequencies()
        collector_seconds = 300
        scriptPath = [k for k in frequencies.keys() if k.endswith("docker-agent.py")]
        if (scriptPath):
            collector_seconds = frequencies[scriptPath[0]]
        # We want inventory every 5 collection cycles  (in minutes)
        performance_frequency = datetime.timedelta(seconds=collector_seconds)
        inventory_frequency = datetime.timedelta(minutes=(collector_seconds * 5) / 60)


        tracker = foglight.model.CollectionTracker(inventory_frequency.seconds)
        if tracker.is_inventory_recommended():
            logger.info("Inventory collection required")
            collect_inventory()
        else:
            collect_performance()

    except:
        logger.error("Unable to establish REST session. Check credentials.")
        logger.error("{0}", traceback.format_exc())
