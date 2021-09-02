# coding=utf-8
"""
查找重复文件

记录文件md5和路径，使用sqllite做记录
多进程加快速度，使用任务队列统筹多个worker间任务平衡
"""

import os
import time
import hashlib
import sqlite3
import redis
import psutil
from multiprocessing import Process, Queue

import MySQLdb

mysqlconf = dict(host="192.168.3.14", port=3306, db="filedata", user="admin", password="&l5D)0hi=rSk_@B", charset='utf8')
workernum = 10


class FileDataBaseSqlite3(object):

    databuff = []

    def __init__(self, dbname, bufsize=200):
        self.dbname = dbname
        self.bufsize = bufsize
        self.db = sqlite3.connect(self.dbname)
        cursor = self.db.cursor()
        cursor.execute("CREATE TABLE IF NOT EXISTS filetable(id INTEGER PRIMARY KEY, name TEXT, fpath TEXT, filemd5 TEXT, filesha1 TEXT, size INTEGER)")
        # cur.executemany('INSERT INTO test VALUES (?,?,?)', [(3, 'name3', 19), (4, 'name4', 26)])

    def addData(self, line):
        """添加数据"""
        self.databuff.append(line)
        if len(self.databuff) > self.bufsize:
            self._commitData()

    def _commitData(self):
        """提交数据"""
        sql = 'INSERT INTO filetable (name, fpath, filemd5, filesha1, size) VALUES (?, ?, ?, ?, ?)'
        cursor = self.db.cursor()
        cursor.executemany(sql, self.databuff)
        self.db.commit()

    def close():
        self._commitData()
        self.cursor.close()
        self.db.close()


class FileDataBaseMysql(object):

    databuff = []

    def __init__(self, dbconf, bufsize=200):
        self.bufsize = bufsize
        self.db = MySQLdb.connect(**dbconf)
        sql = """CREATE TABLE IF NOT EXISTS `filedata` (
                    `id` INT(11) NOT NULL AUTO_INCREMENT,
                    `name` VARCHAR(300) NOT NULL DEFAULT '0',
                    `fpath` VARCHAR(2048) NOT NULL DEFAULT '0',
                    `filemd5` VARCHAR(32) NOT NULL DEFAULT '0',
                    `filesha1` VARCHAR(64) NOT NULL DEFAULT '0',
                    `size` BIGINT(20) NOT NULL DEFAULT 0,
                    PRIMARY KEY (`id`)
                )
                ENGINE=InnoDB"""
        self.db.cursor().execute(sql)

    def addData(self, line):
        """添加数据"""
        self.databuff.append(line)
        if len(self.databuff) > self.bufsize:
            # 每次存入bufsize条数据
            self._commitData()

    def _commitData(self):
        """提交数据"""
        sql = 'INSERT INTO filedata (name, fpath, filemd5, filesha1, size) VALUES (%s, %s, %s, %s, %s)'
        cursor = self.db.cursor()
        cursor.executemany(sql, self.databuff)
        self.db.commit()
        self.databuff = []

    def close():
        self._commitData()
        self.cursor.close()
        self.db.close()


class FileWalker(Process):

    def __init__(self, queue, dirpath=None):
        super(FileWalker, self).__init__()
        if not dirpath:
            self.dirpath = [i.mountpoint for i in psutil.disk_partitions()]
        elif not os.path.isdir(dirpath):
            raise Exception("路径不存在")
        else:
            self.dirpath = [dirpath, ]
        self.queue = queue

    def run(self):
        for diritem in self.dirpath:
            for root, dirs, files in os.walk(diritem):
                for fitem in files:
                    fpath = os.path.join(root, fitem)
                    self.queue.put(fpath, block=True)
                    print(fpath)
        for i in range(workernum):
            self.queue.put("---done---")


class FileSumWorker(Process):

    filedb = FileDataBaseMysql(dbconf=mysqlconf)

    def __init__(self, queue):
        super(FileSumWorker, self).__init__()
        # self.filedb = filedb
        self.queue = queue

    def run(self):
        while True:
            fpath = self.queue.get()
            print(f"read out: {fpath}")
            if fpath == "---done---":
                break
            try:
                data = self._getFileData(fpath)
                self.filedb.addData(data)
            except PermissionError as e:
                print(f"======{e}")
        self.filedb._commitData()

    def _read_chunks(self, fh, size=8096):
        """读文件"""
        fh.seek(0)
        chunk = fh.read(size)
        while chunk:
            yield chunk
            chunk = fh.read(size)

    def _getFileData(self, fpath):
        """获取文件数据"""
        # todo: 尝试异步io
        m = hashlib.md5()
        s = hashlib.sha1()
        with open(fpath, "rb") as f:
            for chunk in self._read_chunks(f):
                m.update(chunk)
                s.update(chunk)
            size = f.tell()
        return (os.path.basename(fpath), fpath, m.hexdigest(), s.hexdigest(), size)


def test():
    queue = Queue(maxsize=200)
    workers = [FileWalker(queue)]
    for i in range(workernum):
        workers.append(FileSumWorker(queue))

    for i, worker in enumerate(workers):
        print(f"===={i}")
        worker.start()

    for worker in workers:
        worker.join()


if __name__ == '__main__':
    test()
