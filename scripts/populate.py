import os
import pyhdfs


if __name__ == '__main__':
    locl_dir = 'C:/Users/dsapo/2023/ddbs/hadoop-3.3.6/articles/'
    hdfs_dir = '/user/dsapo/articles/'

    client = pyhdfs.HdfsClient(hosts=['localhost:9870'], user_name='dsapo')

    dirs = os.listdir(locl_dir)
    client.mkdirs(hdfs_dir)
    for dir in dirs:
        files = os.listdir(locl_dir + dir)
        client.mkdirs(hdfs_dir +  dir)
        for file in files:
            client.copy_from_local(locl_dir + dir + '/' + file, hdfs_dir + dir + '/' + file)
                        
