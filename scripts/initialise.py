import pandas as pd
from pymongo import InsertOne, MongoClient
import numpy as np
import json
from time import time

TEST_RUN = 0
GROUP_SIZE = 20

def db():
    return MongoClient('localhost', 30000).ddbs

def info_over_data(data):
    out_dict = {}
    for i in data:
        if not i['aid'] in out_dict:
            out_dict[i['aid']] = [i['uid']]
        else:
            out_dict[i['aid']].append(i['uid'])
    res_cnt = dict(map(lambda x: (x[0], str(len(x[1]))), out_dict.items()))
    res_set = dict(map(lambda x: (x[0], list(set(x[1]))), out_dict.items()))  
    return res_cnt, res_set

if __name__ == '__main__':
    root_dir = './db-generation/'
    user_path = 'user.dat'
    article_path = 'article.dat'
    read_path = 'read.dat'
    group_size = 10000
    if TEST_RUN:
        group_size = GROUP_SIZE
    group_size_read = 50000
    print('User initialization')
    with open(root_dir + user_path, 'r') as user_file:  # user caching sep based on region 
        cnt, group_dict = 0, {'Beijing': [], 'Hong Kong': []}
        for line in user_file.readlines():
            cnt += 1
            doc = json.loads(line)
            group_dict[doc['region']].append(InsertOne(doc))
            if cnt == group_size:
                if group_dict['Beijing']:
                    db().region_b.bulk_write(group_dict['Beijing'], ordered=True)
                if group_dict['Hong Kong']:
                    db().region_h.bulk_write(group_dict['Hong Kong'], ordered=True)
                cnt = 0
                group_dict['Beijing'], group_dict['Hong Kong'] = [], []
        if cnt > 0:
            if group_dict['Beijing']:
                db().region_b.bulk_write(group_dict['Beijing'], ordered=True)
            if group_dict['Hong Kong']:
                db().region_h.bulk_write(group_dict['Hong Kong'], ordered=True)
    
    print('Article initialization')
    with open(root_dir + article_path, 'r') as article_file:  # same
        cnt, group_dict = 0, {'science': [], 'technology': []}
        for line in article_file.readlines():
            cnt += 1
            doc = json.loads(line)
            group_dict[doc['category']].append(InsertOne(doc))
            if cnt == group_size:
                if group_dict['science']:
                    db().category_s.bulk_write(group_dict['science'], ordered=True)
                if group_dict['technology']:
                    db().category_t.bulk_write(group_dict['technology'], ordered=True)
                cnt = 0
                group_dict['science'], group_dict['technology'] = [], []
        if cnt > 0:
            if group_dict['science']:
                db().category_s.bulk_write(group_dict['science'], ordered=True)
            if group_dict['technology']:
                db().category_t.bulk_write(group_dict['technology'], ordered=True)
    
    print('Read initialization')
    with open(root_dir + read_path, 'r') as f:
        cnt, group_list, uids = 0, [], []
        for line in f.readlines():
            cnt += 1
            doc = json.loads(line)
            uids.append(doc['uid'])
            group_list.append(InsertOne(doc))
            if cnt == group_size_read:
                query, field = {'uid': {'$in': uids}}, {'uid': 1, 'region': 1}
                regions = list(db().region_b.find(query, field)) + list(db().region_h.find(query, field))
                regions = dict(map(lambda x: (x['uid'], x['region']), regions))
                regions = list(map(lambda x: regions[x], uids))
                bj_i = np.argwhere(np.array(regions) == 'Beijing').flatten()  
                hk_i = np.argwhere(np.array(regions) == 'Hong Kong').flatten()
                db().read_b.bulk_write(list(np.array(group_list)[bj_i]), ordered=True)
                db().read_h.bulk_write(list(np.array(group_list)[hk_i]), ordered=True)
                cnt, group_list, uids = 0, [], []
        if cnt > 0:
            query, field = {'uid': {'$in': uids}}, {'uid': 1, 'region': 1}
            regions = list(db().region_b.find(query, field)) + list(db().region_h.find(query, field))
            regions = dict(map(lambda x: (x['uid'], x['region']), regions))
            regions = list(map(lambda x: regions[x], uids))
            bj_i = np.argwhere(np.array(regions) == 'Beijing').flatten()
            hk_i = np.argwhere(np.array(regions) == 'Hong Kong').flatten()
            db().read_b.bulk_write(list(np.array(group_list)[bj_i]), ordered=True)
            db().read_h.bulk_write(list(np.array(group_list)[hk_i]), ordered=True)


    print('Be Read initialization')
    cnt, group_list, group_aids = 0, [], []
    aids = list(db().category_s.find({}, {'aid': 1})) + list(db().category_t.find({}, {'aid': 1}))
    aids = set(map(lambda x: x['aid'], aids))  # all article ids without repetitions
    query, field = {'aid': {'$in': list(aids)}}, {'aid': 1, 'uid': 1}  # return all uids for given aids in pairs
    pairs = list(db().read_b.find(query, field)) + list(db().read_h.find(query, field))
    read_cnt, read_set = info_over_data(pairs)
    query['commentOrNot'] = '1'
    pairs = list(db().read_b.find(query, field)) + list(db().read_h.find(query, field))
    comment_cnt, comment_set = info_over_data(pairs)
    del query['commentOrNot']
    query['agreeOrNot'] = '1'
    pairs = list(db().read_b.find(query, field)) + list(db().read_h.find(query, field))
    agree_cnt, agree_set = info_over_data(pairs)
    del query['agreeOrNot']
    query['shareOrNot'] = '1'
    pairs = list(db().read_b.find(query, field)) + list(db().read_h.find(query, field))
    share_cnt, share_set = info_over_data(pairs)
    for aid in aids:
        cnt += 1
        group_aids.append(aid)
        art_dict = {
            'id': f'br{aid}',
            'timestamp': str(round(time() * 1e3)),
            'aid': aid,
            'readNum': read_cnt[aid],
            'readUidList': read_set[aid],
            'commentNum': comment_cnt[aid],
            'commentUidList': comment_set[aid],
            'agreeNum': agree_cnt[aid],
            'agreeUidList': agree_set[aid],
            'shareNum': share_cnt[aid],
            'shareUidList': share_set[aid]
        }
        group_list.append(InsertOne(art_dict))
        if cnt == group_size:
            query, field = {'aid': {'$in': group_aids}}, {'category': 1}
            categories = list(db().category_s.find(query, field)) + list(db().category_t.find(query, field))
            print(categories[0])
            print(categories[0]['category'])
            categories = list(map(lambda x: x['category'], categories))
            s_i = np.argwhere(np.array(categories) == 'science').flatten()
            t_i = np.argwhere(np.array(categories) == 'technology').flatten()
            db().read_cat_s.bulk_write(list(np.array(group_list)[s_i]), ordered=True)
            db().read_cat_t.bulk_write(list(np.array(group_list)[t_i]), ordered=True)
            cnt, group_list, group_aids = 0, [], []
    if cnt > 0:
        query, field = {'aid': {'$in': group_aids}}, {'category': 1}
        categories = list(db().category_s.find(query, field)) + list(db().category_t.find(query, field))
        categories = list(map(lambda x: x['category'], categories))
        s_i = np.argwhere(np.array(categories) == 'science').flatten()
        t_i = np.argwhere(np.array(categories) == 'technology').flatten()
        db().read_cat_s.bulk_write(list(np.array(group_list)[s_i]), ordered=True)
        db().read_cat_t.bulk_write(list(np.array(group_list)[t_i]), ordered=True)

    if TEST_RUN:
        exit(0)

    print('Popularity Rank initialization')
    with open(root_dir + read_path, 'r') as f:  
        ranks = {'daily': {}, 'weekly': {}, 'monthly': {}}
        for line in f.readlines():
            item = json.loads(line)
            t = pd.to_datetime(int(item['timestamp']), unit='ms')
            all_ts_formats = {
                'daily': f'{t.day}/{t.month}/{t.year}',
                'weekly': f'{t.week}/{t.year}',
                'monthly': f'{t.month}/{t.year}'
            }
            for dmw in ranks.keys():
                ts_format = all_ts_formats[dmw]
                if ts_format not in ranks[dmw]:
                    ranks[dmw][ts_format] = {}
                if item['aid'] not in ranks[dmw][ts_format]:
                    ranks[dmw][ts_format][item['aid']] = 0
                ranks[dmw][ts_format][item['aid']] += 1

        cnt = 0
        insert_dict = {'daily': [], 'weekly': [], 'monthly': []}
        formats_dict = {'daily': '%d/%m/%Y', 'weekly': "%w/%W/%Y", "monthly": "%m/%Y"}
        prefix_dict = {'daily': '', 'weekly': "0/", "monthly": ""}
        for dmw in ranks.keys():
            for tm in ranks[dmw]:
                ranks[dmw][tm] = sorted(ranks[dmw][tm].items(), key=lambda x: x[1], reverse=True)
                ranks[dmw][tm] = list(map(lambda x: x[0], ranks[dmw][tm]))
                article_dict = {
                    'id': f'pr{cnt}',
                    'temporalGranularity': dmw,
                    'articleAidList': ranks[dmw][tm],
                    'timestamp': str(pd.to_datetime(prefix_dict[dmw] + tm, format=formats_dict[dmw]).value // 1e6)
                }
                insert_dict[dmw].append(InsertOne(article_dict))
                cnt += 1

    db().popular_d.bulk_write(list(insert_dict['daily']), ordered=True)
    db().popular_w.bulk_write(list(insert_dict['weekly']), ordered=True)
    db().popular_m.bulk_write(list(insert_dict['monthly']), ordered=True)
