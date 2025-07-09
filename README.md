apiVersion: keda.sh/v1alpha1

kind: TriggerAuthentication

metadata:

  name: mongo-trigger-auth
  
spec:

  secretTargetRef:
  
  - parameter: connectionString
    
    name: mongo-secret
    
    key: uri
----------------------------------------------------------------------------------------------------------------

apiVersion: keda.sh/v1alpha1

kind: ScaledObject

metadata:

  name: mongo-worker-scaler
  
spec:

  scaleTargetRef:
  
    name: mongo-worker
    
  minReplicaCount: 1
  
  maxReplicaCount: 10
  
  pollingInterval: 10         # seconds between checks
  
  cooldownPeriod:  30         # seconds to wait before scale down
  
  triggers:
  
  - type: mongodb
    
    metadata:
    
      dbName: mydatabase
    
      collection: records
    
      query: '{"status": "new"}'
    
      connectionStringFromEnv: MONGO_URI
    
      threshold: "5"           # scale out if more than 5 unprocessed records
    
    authenticationRef:
    
      name: mongo-trigger-auth
