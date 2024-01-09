docker-compose -f dockers/caching.yml down -v

docker-compose -f dockers/servers.yml down -v
docker-compose -f dockers/shards.yml down -v
docker-compose -f dockers/instance.yml down -v
