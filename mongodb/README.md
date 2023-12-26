# MONGO setup instructions

## To Setup Servers 
To apply the docker configuration run:
````
docker-compose -f mongodb/compose/servers.yml up -d
````

To check the correctness run the following:
````
docker-compose -f mongodb/compose/servers.yml ps
````

Use the Mongo client application to log into each one of the config server replicas:
````
mongo mongodb://localhost:[port]
````

Initiate the replicas in MongoDB (but instead of 192.168.124.7 use your local id):

````
rs.initiate(
  {
    _id: "cfgrs",
    configsvr: true,
    members: [
      { _id : 0, host : "192.168.124.7:10001" },
      { _id : 1, host : "192.168.124.7:10002" }
    ]
  }
)
````
If the operation is successful, the "ok" value in the output is 1

You can use the following method to check the status of your instances:
````
rs.status() 
````

## To Setup Shards
To apply the docker configuration run:
````
docker-compose -f mongodb/compose/shards.yml up -d
````

To check the correctness run the following:
````
docker-compose -f mongodb/compose/shards.yml ps
````

Use the Mongo client application to log into each one of the config server replicas:
````
mongo mongodb://localhost:[port]
````

Initiate the replicas in MongoDB (but instead of 192.168.124.7 use your local id):

````
rs.initiate(
  {
    _id: "shard1rs",
    members: [
      { _id : 0, host : "192.168.124.7:20001" },
      { _id : 1, host : "192.168.124.7:20002" }
    ]
  }
)
````
If the operation is successful, the "ok" value in the output is 1

You can use the following method to check the status of your instances:
````
rs.status() 
````

## To Setup a Mongos Instance




