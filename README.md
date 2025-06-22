**Architecture Overview**

This application implements a dynamic MongoDB workload processor using a custom Kubernetes Operator written in Python.

***Core Components***

**MongoDBQueue CRD**

A custom resource definition that represents a unit of work derived from MongoDB records.

**watcher.py**

A standalone Python script that continuously polls a MongoDB collection for records with status: "waiting". Based on the current load (number of waiting records), it creates corresponding MongoDBQueue custom resources in the cluster.

**Python Custom Operator**

Implemented using the kopf framework , this operator watches for new MongoDBQueue resources and responds by launching Kubernetes Jobs to process them.

**Kubernetes Job (Worker)**

For every new MongoDBQueue resource, a temporary Job is created. This Job:

-Reads and processes the associated MongoDB record(s)

-Updates the record’s status in MongoDB to "completed" or "failed"

-Terminates after processing is complete


![Custom-Operator](https://github.com/user-attachments/assets/aff85aef-e29c-4063-8ddb-516c8bfbf1a2)
