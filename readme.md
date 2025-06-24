editpart  - mongo uri in opp_dep.yaml
          - mongo uri in worker_job.yaml

deploy.sh - for deploying on minikube

sorry for the naming 

retry functionality still needs to be implemented

mapping - 1 record --- 1 job 

#passing the mongo uri from the operator to the job can be skipped.
basic explanation

mongo_scaler_operator looks for change in db every x seconds (x can be changed from line 55)
                        |
if records are pushed it will start equivalent number of jobs 
                        |
each job spans a pod which runs the worker image
                        |
the image self claims an unfinished task by updating the flag (atomic)
                        |
the image does the processing and exits


#example entry
db.records.insertOne({
  "status": "new",
  "retryCount": 0,
  "payload": {
    "message": "Hello from Citi!"
  }
})

**Architecture**

![K8s_operator(2)](https://github.com/user-attachments/assets/7ebfebe4-ff5d-4cb1-898c-77fc1d78bf19)

