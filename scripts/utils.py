from bson import json_util
import numpy as np
import redis


def cache_init():  # todo change hyperpars?
    cache = redis.Redis(host='192.168.124.7', port=6379)
    cache.config_set('maxmemory', '100mb')
    cache.config_set('maxmemory-policy', 'allkeys-lru')
    return cache

def cache_find(query, field, id, id_name, entity, attributes):  # todo understan and change non pos pos stuff
    cache = cache_init()
    ids = id.split()
    parsed_ids = list(map(lambda x: f'{entity}_{x}', ids))
    cache_res = cache.mget(parsed_ids)
    cache_res = list(map(lambda x: json_util.loads(x.decode('utf-8')) if x else None, cache_res))
    none_cache = np.argwhere(np.array(cache_res) == None).flatten()
    real_cache = np.argwhere(np.array(cache_res) != None).flatten()
    found = []
    if none_cache.shape[0]:
        ids = list(np.array(ids)[none_cache])
        query[id_name] = {'$in': ids}
        for attribute in attributes:
            found += list(attribute.find(query, field))
        if len(ids) == len(found):
            parsed_uids = list(map(lambda x: f'{entity}_{x}', ids))
            parsed_jsons = list(map(lambda x: json_util.dumps(x), found))
            cache.mset(dict(zip(parsed_uids, parsed_jsons)))
    return found + list(np.array(cache_res)[real_cache])
