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

To apply the docker configuration run:
````
docker-compose -f mongodb/compose/instance.yml up -d
````

To check the correctness run the following:
````
docker-compose -f mongodb/compose/instance.yml ps
````

Use the Mongo client application to connect to the sharded cluster:
````
mongo mongodb://localhost:[mongos-port]
````

Use the sh.addshard() method and connect the shard replicas to the cluster:

````
sh.addShard("shard1/192.168.124.7:20001,192.168.124.7:20004")
````

Add the shared shard
````
sh.addShard( "shard1/192.168.124.7:20002,192.168.124.7:20003")
````

Check the status with the sh.status() method:

````
sh.status() 
````

##  Enable Sharding for the Database

For this project, we use $use demo$ ddbs
````
sh.enableSharding("ddbs") 
````

## Setup Collection Sharding

TODO

It's about 
````
region= ”Beijing”  allocated in DBMS1,       
region= “HongKong” allocated in DBMS2.
````
 
and stuff