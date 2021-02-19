#coding=utf-8

import os
import json
import hashlib
import shutil


def read_chunks(fh, size=8096):
    """读文件"""
    fh.seek(0)
    chunk = fh.read(size)
    while chunk:
        yield chunk
        chunk = fh.read(size)
    else:
        fh.seek(0)


class JEncoder(json.encoder.JSONEncoder):
    """docstring for JENcoder"""

    def default(self, o):
        try:
            iterable = iter(o)
        except TypeError:
            pass
        else:
            return list(iterable)
        return JSONEncoder.default(self, o)
        


class FileItem(object):
    """
    文件项

    记录文件路径、md5、sha1、大小
    """

    def __init__(self, fpath):
        """初始化"""
        super(FileItem, self).__init__()
        if not os.path.isfile(fpath):
            raise Exception(f"文件不存在: {fpath}")
        self.fpath = fpath
        self.fsize = os.path.getsize(fpath)
        self.getHash()

    def getHash(self):
        """获取文件的hash值"""
        m = hashlib.md5()
        s = hashlib.sha1()
        with open(self.fpath, "rb") as f:
            for chunk in read_chunks(f):
                m.update(chunk)
                s.update(chunk)
        self.md5 = m.hexdigest()
        self.sha1 = s.hexdigest()

    def getDetail(self):
        """详细信息"""
        return f"{self.md5}-{self.sha1}", {"filepath": self.fpath, "filesize": self.fsize,
                                           "md5": self.md5, "sha1": self.sha1}


def getFileData(dirpath):
    """
    遍历路径

    格式：
        {key: {fileitem}}
    """
    if not os.path.isdir(dirpath):
        raise Exception("需要正确的目录路径")

    filedata = {}
    repeat = {}
    num = 0
    for d, dl, fl in os.walk(dirpath):
        for f in fl:
            fpath = os.path.join(d, f)
            k, v = FileItem(fpath).getDetail()
            if k in filedata:
                print(f"文件重复: {fpath}")
                repeat[k] = repeat.get(k, set())
                repeat[k].add(fpath)
                repeat[k].add(filedata[k].get("filepath", ""))
                continue
            filedata[k] = v
            num += 1
            print(f"{num}: {fpath}")
    filedata["repeat"] = repeat
    return filedata


def geneJsonFile(dirpath, filedata):
    """生成json"""
    jsonfile = os.path.join(dirpath, "filedata.json")
    if os.path.exists(jsonfile):
        raise Exception("文件已存在")

    with open(jsonfile, "w") as f:
        json.dump(filedata, f, indent=4, cls=JEncoder)
    return jsonfile


def checkDir(srcdir, tgtdir, jsonfile=None):
    """检查路径，拷贝文件"""
    if not os.path.isdir(srcdir):
        raise Exception("需要正确的源目录路径")

    if not os.path.isdir(tgtdir):
        raise Exception("需要正确的目标目录路径")

    if os.listdir(tgtdir):
        raise Exception("目标目录必须为空")

    if not jsonfile:
        jsonfile = os.path.join(srcdir, "filedata.json")

    if not os.path.isfile(jsonfile):
        raise Exception("找不到json文件")

    filedata = json.load(open(jsonfile, "r"))
    num = 0
    filelist = []
    for d, dl, fl in os.walk(srcdir):
        for f in fl:
            fpath = os.path.join(d, f)
            k, v = FileItem(fpath).getDetail()
            if k in filedata:
                # 文件存在
                continue
            relative = fpath.replace(srcdir, "", 1).strip(os.path.sep)
            tgtpath = os.path.join(tgtdir, relative)
            tmpdir = os.path.dirname(tgtpath)
            if not os.path.exists(tmpdir):
                os.makedirs(tmpdir)
            shutil.copy(fpath, tgtpath)
            num += 1
            print(f"{num}-{tgtpath}")
            filelist.append(relative)
    return filelist


def gatherDirData():
    """采集目录内容"""
    dirpath = input("输入文件路径:")
    jsonfile = geneJsonFile(dirpath, getFileData(dirpath))


def syncAndCopy():
    dirpath = input("输入文件路径:")
    jsonfile = os.path.join(dirpath, "filedata.json")
    jsonfile = input(f"输入json文件路径(默认{jsonfile}):").strip()
    tgtdir = input("输入目标目录路径:")
    checkDir(dirpath, tgtdir, jsonfile)


def main():
    """
    获取文件
    """
    instro = "请选择需要的操作：\t\n1.生成目录数据\t\n2.复制文件\t\n3.退出\n:"
    p = input(instro)
    while p != "3":
        if p == "1":
            gatherDirData()
        elif p == "2":
            syncAndCopy()
        else:
            print("无此项\n")
        p = input(instro)


def test():
    return geneJsonFile("E:/music", getFileData("E:/music"))


if __name__ == '__main__':
    main()