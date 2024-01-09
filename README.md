# Distributed Database Systems Final Project
Final Project by

Sapozhnikova Daria 2022280382 & Bulatova Ekaterina 2022280381

# Important notice

This project is build to work one one windows machine, no virtual machines needed. 

# Prerequisites

To successfully run this project, those libraries and containers have to be preinstalled
 
* Docker
* Redis
* MangoDB
* MongoDB Compass
* Hadoop
* Java JDK 
* WSL


# Installation Guide

## Hadoop

In this part we will be manually aeting up a one-node cluster on our machine using instructions from [this tutorial](https://www.youtube.com/watch?v=FAly8HaYkbQ&t=2s) and code from [this tutorial](https://towardsdatascience.com/installing-hadoop-3-1-0-multi-node-cluster-on-ubuntu-16-04-step-by-step-8d1954b31505)

### System configuration

Make sure that you have both [Hadoop](https://hadoop.apache.org/releases.html) and [Java JDK](https://www.oracle.com/java/technologies/downloads/) installed

Inside the hadoop folder create a folder "data" with subfolders "datanode", "namenode" and "temp"

Inside the hadoop folder create a folder "local" 

Set envirionmental variables: add variables "JAVA_HOME" and "HADOOP_HOME" using the path to the installed Java JDK and Hadoop, add "%JAVA_HOME%", "%JAVA_HOME%\bin", "%JAVA_HOME%\sbin" ,"HADOOP_HOME", "%HADOOP_HOME%\sbin" and "%HADOOP_HOME%\bin" to the Path

### Edit hadoop configuration

Go to "etc\hadoop" in the hadoop folder

#### Edit core-site.xml

Change the configuraion in the following file

````
<configuration>
<property>
<name>fs.defaultFS</name>
<value>hdfs://hadoop-namenode:9820/</value>
<description>NameNode URI</description>
</property>
<property>
<name>io.file.buffer.size</name>
<value>131072</value>
<description>Buffer size</description>
</property>
</configuration>
````

#### Edit hdfs-site.xml

Change the configuraion in the following file (Path is the path to the newly created data folder)

````
<configuration>
<property>
<name>dfs.namenode.name.dir</name>
<value>[Path]/namenode</value>
<description>NameNode directory for namespace and transaction logs storage.</description>
</property>
<property>
<name>dfs.datanode.data.dir</name>
<value>[Path] /datanode</value>
<description>DataNode directory</description>
</property>
<property>
<name>dfs.replication</name>
<value>3</value>
</property>
<property>
<name>dfs.permissions</name>
<value>false</value>
</property>
<property>
<name>dfs.datanode.use.datanode.hostname</name>
<value>false</value>
</property>
<property>
<name>dfs.namenode.datanode.registration.ip-hostname-check</name>
<value>false</value>
</property>
</configuration>
````


#### Edit yarn-site.xml

Change the configuraion in the following file ([Hadoop-path] is the path to the hadoop folder)

````
<configuration>
<property>
<name>yarn.nodemanager.aux-services</name>
<value>mapreduce_shuffle</value>
<description>Yarn Node Manager Aux Service</description>
</property>
<property>
<name>yarn.nodemanager.aux-services.mapreduce.shuffle.class</name>
<value>org.apache.hadoop.mapred.ShuffleHandler</value>
</property>
<property>
<name>yarn.nodemanager.local-dirs</name>
<value>[Hadoop-path]/local</value>
</property>
<property>
<name>yarn.nodemanager.log-dirs</name>
<value>[Hadoop-path]/logs</value>
</property>
</configuration>
````


#### Edit mapred-site.xml

Change the configuraion in the following file


````
<configuration>
<property>
<name>mapreduce.framework.name</name>
<value>yarn</value>
<description>MapReduce framework name</description>
</property>
<property>
<name>mapreduce.jobhistory.address</name>
<value>hadoop-namenode:10020</value>
<description>Default port is 10020.</description>
</property>
<property>
<name>mapreduce.jobhistory.webapp.address</name>
<value> hadoop-namenode:19888</value>
<description>Default port is 19888.</description>
</property>
<property>
<name>mapreduce.jobhistory.intermediate-done-dir</name>
<value>/mr-history/tmp</value>
<description>Directory where history files are written by MapReduce jobs.</description>
</property>
<property>
<name>mapreduce.jobhistory.done-dir</name>
<value>/mr-history/done</value>
<description>Directory where history files are managed by the MR JobHistory Server.</description>
</property>
</configuration>
````

#### Edit hadoop-env.cmd

Set JAVA_HOME path using your exsisting JAVA_HOME path "C:\Program Files\..." as "C:\PROGRA~1\..."
to avoid spaces in the name

#### Edit workers

Let the namenode know the number of workers by witing this in the workers file

````
hadoop-namenode
hadoop-datanode2
````

#### Edit system hosts

Open "C:\Windows\System32\drivers\etc\hosts" as an administrator and add follwoing lines to the end of the file

````
127.0.0.1   hadoop-namenode
[chosen-ip] hadoop-datanode2

````

*NB* Fre space between ip and a worker name is actually a tabulation, double check that the format is transferred correctly

*NB* A part of docker may be occupying the 127.0.0.1 ip, but for the time of this project you can comment this line in the file, it won't affect the performance. Just don't forget to reverse it after you are done.

#### Edit core-site.xml

Change the configuraion in the following file

#### Replace hadoop bin folder

Download the bin folder that is compatible with windown from [this website](https://github.com/cdarlint/winutils). Choose the latest version that does not exceed your hadoop version. 

Replace the bin folder in the hadoop folder with the new one.

#### Add new activation JAR file

Download the windows activation jar file from [this link](https://www.youtube.com/redirect?event=video_description&redir_token=QUFFLUhqa0NKdDRrdXpEWFJITXhtalNONjFkVUhna1dCQXxBQ3Jtc0trSk96WUNxaHJhcTNXMEtSTVFqbHZaQ0VaNXl0TklLS2NPRlhNUlZ0UzBkcTFWS1QxenlTNUxQeGgzTkg2eGdwdmRacGJfcFg0N0E0eDRvRWxvdmxIVEVxck01bVV3X1dST1QwbnhYeF9OcFBNcndGUQ&q=https%3A%2F%2Frepo1.maven.org%2Fmaven2%2Fjavax%2Factivation%2Factivation%2F1.1.1%2Factivation-1.1.1.jar&v=FAly8HaYkbQ)

Put this file in the "share\hadoop\common\" directory of your hadoop folder

### Start the hadoop

To format the namenode, run the following command as an administrator

````
hdfs namenode –format
````

or 

````
hadoop namenode –format
````

After that start all the nodes using the following command as an administrator

````
start-all
````

### Transfer data

To end up Hadoop set up, transfer data to the node. For this run the following command

````
python -m scripts.populate
````

### Monitoring

You can check your datanode information by accessing http://localhost:9870/

You can check general hadoop information by accessing http://localhost:8088/

You can browse files by accessing http://localhost:9870/explorer.html#/


## Docker

*NB* For this you need to install WSL (version 1.1.3.0 or later) in advance. In this project we are using Ubuntu 22.04.3 LTS.

Download and install the latest version of [Docker](https://docs.docker.com/desktop/install/windows-install/)



## MongoDB

This part of the manual is based on  [this tutorial](https://phoenixnap.com/kb/mongodb-sharding) 

### To Setup Servers 
To apply the docker configuration run:
````
docker-compose -f dockers/servers.yml up -d
````


Use the Mongo client application to log into one of the config server replicas for ports 10001, 10002:
````
mongosh [your-ip]:[port]
````

Initiate the replicas in MongoDB:

````
rs.initiate({_id: "cfgrs",configsvr: true,members: [{ _id : 0, host : "[your-ip]:10001" },{ _id : 1, host : "[your-ip]:10002" }]})
````
If the operation is successful, the "ok" value in the output is 1

You can use the following method to check the status of your instances:
````
rs.status() 
````

### To Setup Shards
To apply the docker configuration run:
````
docker-compose -f dockers/shards.yml up -d
````

For each of the ports (20001 and 20004), use the Mongo client application to log each into one of not shared the config server replicas :
````
mongosh [your-ip]:[port]
````

Initiate the replicas in MongoDB

````
rs.initiate({_id: "shard1rs", members: [{ _id : 0, host : "[your-ip]:[port]" }]})
````


Afterwards, do the same with the shared shard. Use the Mongo client application to log into  the config server replica:

````
mongosh [your-ip]:[port]
````

Initiate the replica in MongoDB:

````
rs.initiate({_id: "shard3rs", members: [{ _id : 0, host : "[your-ip]:20002" }, { _id : 1, host : "[your-ip]:20003" }]})
````

### To Setup a Mongos Instance

To apply the docker configuration run:
````
docker-compose -f dockers/instance.yml up -d
````



Use the Mongo client application to connect to the sharded cluster (in this project, mongos-port is set to bee 30000):
````
mongosh mongodb://[your-ip]:[mongos-port]
````


Use the sh.addshard() method and connect the shard replicas to the cluster:

````
sh.addShard("shard1rs/[your-ip]:20001")
sh.addShard("shard2rs/[your-ip]:20004")
````

Add the shared shard
````
sh.addShard( "shard3rs/[your-ip]:20002,[your-ip]:20003")
````

Check the status with the sh.status() method:

````
sh.status() 
````

####  Enable Sharding for the Database

For this project, we use $use demo$ ddbs

````
use ddbs
sh.enableSharding("ddbs") 
````

#### Associates a shard with an  identifier. 

Set an identifier to direct chunks that fall within a tagged range to specific shards.

````
sh.addShardTag("shard1rs", "shard1")
sh.addShardTag("shard2rs", "shard2")
sh.addShardTag("shard3rs", "shard3")
````

### Setup Collection Sharding

For each fragment run collection initialisation

````
sh.shardCollection("ddbs.[name]", { 'uid': 1 } )
sh.addTagRange( 
  "ddbs.[name]",
  { "uid" : MinKey },
  { "uid" : MaxKey },
  "[Server]"
)

sh.addTagRange( "ddbs.[name]",{ "uid" : MinKey },{ "uid" : MaxKey },"[Server]")
````

Where pairs of collections and servers are as given

* region_b - shard1
* region_h - shard2
* category_s - shard3
* category_t - shard2
* read_b - shard1
* read_h - shard2
* read_cat_s - shard3
* read_cat_t - shard2
* popular_d - shard1
* popular_w - shard2
* popular_m - shard3

After setting up the collections, exit Mongosh

### Transfer data

To end up MongoDB set up, transfer data managment system. For this run the following command

````
python -m scripts.initialise
````

## Redis

The instructions are based on [this official tutorial](https://redis.io/docs/install/install-redis/install-redis-on-windows/)

*NB* If a line has to be run via wsl, there will be a *WSL* note before the explanation  

*WSL* First of all, start the redis server

````
sudo service redis-server start
````

We will start running the redis server on top of docker via executing this

````
 docker-compose -f dockers/caching.yml up  -d
````


*WSL* To access the rever run the following command 

````
redis-cli -h 192.168.124.7 -p 6379
````

*WSL* To check the correctness ping the server (PONG is the expected answer from the server)

````
192.168.124.7:6379> ping
PONG
192.168.124.7:6379> exit
````

*WSL* Initialize the limitations of the container (memory limit and frequency-based deletions)

````
CONFIG SET maxmemory 100mb
CONFIG SET maxmemory-policy allkeys-lfu
````



## Run the application

To run the application run the following line

````
python -m application.app_stylish
````



## Delete everything

To finish working run

````
docker-compose -f mongodb/compose/servers.yml down -v
docker-compose -f mongodb/compose/shards.yml down -v
docker-compose -f mongodb/compose/instance.yml down -v
```


