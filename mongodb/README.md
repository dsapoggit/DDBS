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

Use the Mongo client application to log into one of the config server replicas for ports 10001, 10002:
````
mongosh localhost:[port]
mongosh 192.168.124.7:10001
````

Initiate the replicas in MongoDB (but instead of 192.168.124.7 use your local id):

````
rs.initiate({_id: "cfgrs",configsvr: true,members: [{ _id : 0, host : "192.168.124.7:10001" },{ _id : 1, host : "192.168.124.7:10002" }]})
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

Use the Mongo client application to log each into one of not shared the config server replicas (20001 and 20004):
````
mongosh localhost:[port]
mongosh 192.168.124.7:20001
mongosh 192.168.124.7:20004
````

Initiate the replicas in MongoDB (but instead of 192.168.124.7 use your local id):

````
rs.initiate({_id: "shard1rs", members: [{ _id : 0, host : "192.168.124.7:20001" }]})
````

and
````
rs.initiate({_id: "shard2rs", members: [{ _id : 1, host : "192.168.124.7:20004" }]})
````

Do the same with the shared shard

````
mongosh localhost:[port]
mongosh 192.168.124.7:20002
````


Initiate the replicas in MongoDB (but instead of 192.168.124.7 use your local id):

````
rs.initiate({_id: "shard3rs", members: [{ _id : 0, host : "192.168.124.7:20002" }, { _id : 1, host : "192.168.124.7:20003" }]})
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
mongosh mongodb://localhost:[mongos-port]
mongosh 192.168.124.7:30000
````


Use the sh.addshard() method and connect the shard replicas to the cluster:

````
sh.addShard("shard1rs/192.168.124.7:20001")
sh.addShard("shard2rs/192.168.124.7:20004")
````

Add the shared shard
````
sh.addShard( "shard3rs/192.168.124.7:20002,192.168.124.7:20003")
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

### Fragmentation based on the region attribute

````
region= ”Beijing”  allocated in DBMS1,       
region= “HongKong” allocated in DBMS2.
````

For Beijing users run this

````
sh.shardCollection("ddbs.region_b", { [field]: 1 } )
sh.addTagRange( 
  "ddbs.region_b",
  { "uid" : MinKey },
  { "uid" : MaxKey },
  "shard0"
)
````

For Hong Kong users run this

````
sh.shardCollection("ddbs.region_h", { [field]: 1 } )
sh.addTagRange( 
  "ddbs.region_h",
  { "uid" : MinKey },
  { "uid" : MaxKey },
  "shard2"
)
````


### Fragmentation based on the category attribute

````
category=”science”     allocated in DBMS1 and DBMS2,     
category=“technology”  allocated in DBMS2
````

For scientific articles run this

````
sh.shardCollection("ddbs.category_s", { [field]: 1 } )
sh.addTagRange( 
  "ddbs.category_s",
  { "uid" : MinKey },
  { "uid" : MaxKey },
  "shard3"
)
````

For technology articles run this

````
sh.shardCollection("ddbs.category_t", { [field]: 1 } )
sh.addTagRange( 
  "ddbs.category_t",
  { "uid" : MinKey },
  { "uid" : MaxKey },
  "shard2"
)
````


### Fragmentation based on the User table without replica

TODO 

Don't understand


### Fragmentation based on the Article table with duplication

````
category=”science”     allocated in DBMS1 and DBMS2,     
category=“technology”  allocated in DBMS2
````


### Fragmentation based on the temporal granularity

````
temporalGranularity=“daily”              allocated to DBMS1,       
temporalGranularity=“weekly”or “monthly” allocated to DBMS2.

````

## Delete everything

To finish working run

````
docker-compose -f mongodb/compose/servers.yml down -v
docker-compose -f mongodb/compose/shards.yml down -v
docker-compose -f mongodb/compose/instance.yml down -v
````