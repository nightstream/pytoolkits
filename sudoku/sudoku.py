#coding=utf-8
"""解数独"""


class Sudoku(object):
    """数独"""

    # _DISDATA: 格式 {1: {2: [7, 8]}}
    #           代表坐标(1, 2)内的数字不能是7和8
    _DISDATA = {}
    _RESULT = {}
    _runinfo = [0, 0]

    def __init__(self, data, step=True):
        """初始化"""
        for x in range(9):
            for y in range(9):
                self._setValue(x, y, data[x][y])
        self.step = step

    def run(self):
        """执行运算"""
        self.livediff = True  # 数值有发生变化
        while self.livediff:
            self.livediff = False
            for x in range(9):
                for y in range(9):
                    self.doStep(x, y)
        print(self)

    def _makeDefault(self, x, y):
        """
        resule坐标(x, y)值为0

        _DISDATA坐标(x, y)禁用值为set()
        """
        self._DISDATA[x] = self._DISDATA.get(x, {})
        self._DISDATA[x][y] = self._DISDATA[x].get(y, set())

    def _makeCheck(self, x, y, value):
        """
        resule坐标(x, y)值为value

        _DISDATA坐标(x, i)禁用值为 _DISDATA[x][i].add(value)
        _DISDATA坐标(i, y)禁用值为 _DISDATA[x][i].add(value)
        """
        # 计算行列
        for i in range(9):
            self._DISDATA[x] = self._DISDATA.get(x, {})
            self._DISDATA[x][i] = self._DISDATA[x].get(i, set())
            self._DISDATA[i] = self._DISDATA.get(i, {})
            self._DISDATA[i][y] = self._DISDATA[i].get(y, set())
            if i != x:
                self._DISDATA[i][y].add(value)
            if i != y:
                self._DISDATA[x][i].add(value)

        # 计算九宫
        f = lambda x: range(x//3*3, (x//3+1)*3)
        for ix in f(x):
            for iy in f(y):
                if ix == x and iy == y:
                    # 当前单元格
                    continue
                
                self._DISDATA[ix] = self._DISDATA.get(ix, {})
                self._DISDATA[ix][iy] = self._DISDATA[ix].get(iy, set())
                self._DISDATA[ix][iy].add(value)

        self._DISDATA[x][y] = set(range(1, 10)) - set([value])

    def _setValue(self, x, y, value):
        """设置值"""
        if value == 0:
            # 需要计算
            self._makeDefault(x, y)
        else:
            # 需要排除
            self._makeCheck(x, y, value)
        self._RESULT[x] = self._RESULT.get(x, {})
        self._RESULT[x][y] = value
        self.livediff = True

    def _getValue(self, x, y):
        """获取值"""
        return self._RESULT.get(x, {}).get(y, 0)

    def gatherNum(self, x, y):
        """整理已有数据"""
        # 计算行列，收集其他行列和九宫内已被禁用的数字
        _col = set(range(1, 10)) - self._DISDATA[x][y]
        _row = set(range(1, 10)) - self._DISDATA[x][y]
        for i in range(9):
            if i != y and self._getValue(x, i) == 0:
                _col &= self._DISDATA[x][i]  # 列
            if i != x and self._getValue(i, y) == 0:
                _row &= self._DISDATA[i][y]  # 行
        if len(_col) == 1:
            return _col
        if len(_row) == 1:
            return _row

        # 计算九宫，收集九宫中已有的数字
        _cells = set(range(1, 10)) - self._DISDATA[x][y]
        f = lambda x: range(x//3*3, (x//3+1)*3)
        for ix in f(x):
            for iy in f(y):
                if ix == x and iy == y:
                    # 当前单元格
                    continue
                if self._getValue(ix, iy) > 0:
                    continue
                _cells &= self._DISDATA[ix][iy]
        return _cells

    def doStep(self, x, y, trace=False):
        """单步录入"""
        self._runinfo[1] += 1
        if trace:
            import pdb;pdb.set_trace()
        if self._getValue(x, y) > 0:
            return
        _all = list(self.gatherNum(x, y))
        if len(_all) != 1:
            return
        self._setValue(x, y, _all[0])
        self._runinfo[0] += 1
        if self.step:
            s = input(f"回车执行下一步({x}, {y}) {_all}:")
            print(self)

    def __repr__(self):
        def getLine(x):
            l = []
            for i in range(9):
                l.append(self._getValue(x, i))
            return l
        lines = []
        fmtstr = "{} " * 9
        for i in range(9):
            lines.append(fmtstr.format(*getLine(i)).strip())
        lines.append("操作: {} / {}".format(*self._runinfo))
        return "\n".join(lines)

    def __str__(self):
        return self.__repr__()


def getQuestion(content):
    """获取题目"""
    import re
    l = []
    regx_line = re.compile(r"\|[\.\d\ ]+\|[\.\d\ ]+\|[\.\d\ ]+\|")
    for line in content.splitlines():
        i = regx_line.findall(line)
        if not i:
            continue
        l.append([int(a) for a in i[0].replace("|", "").replace(".", "0").split(" ") if a])
    return l


def main():
    data = getQuestion("""+-------+-------+-------+       k
                           | . . . | . 6 . | 5 8 . |     h   l move cursor
                           | 3 . 6 | 2 . . | . . . |       j
Rules:                     | 9 . . | . . 5 | . 2 . |      1-9  place digit
                           +-------+-------+-------+      0 .  clear digit
 Fill the grid so that     | . . 3 | . 9 . | . 5 . |       c   clear board
 every column, row and     | 4 . . | 5 . 6 | . . 1 |       f   fix squares
 3x3 box contains each     | . 1 . | . 7 . | 6 . . |       n   new board
 of the digits 1 to 9.     +-------+-------+-------+       q   quit game
                           | . 6 . | 9 . . | . . 3 |       s   save
                           | . . . | . . 8 | 4 . 5 |       r   restart
                           | . 3 7 | . 1 . | . . . |       u   undo last move
                           +-------+-------+-------+       v   solve
""")

    s = Sudoku(data, step=False)
    s.run()
    return s

if __name__ == '__main__':
    main()
