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


![Updated_operator(1)](https://github.com/user-attachments/assets/00c185f0-0e8d-4eb6-9e63-32df1f76d6e9)


**Future Improvements:**


The current setup creates Jobs as needed, but it doesn't control how many run at the same time. In the future, the Operator can be improved to always keep at least 3 Jobs running and limit the maximum to 10 based on the load. Also, instead of using short-lived Jobs, we could switch to long-running Pods or Deployments that keep checking MongoDB and processing tasks without restarting each time
