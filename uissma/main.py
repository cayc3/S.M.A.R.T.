# -*- coding: utf-8 -*-

from PyQt4 import QtGui, QtCore, Qt
from MS_MainWindow import Ui_MainWindow
import sys, os, shutil
from control import CheckFolder, ScanFile
from checkthread.StartUI import MainWindow as detailwindow

reload(sys)
sys.setdefaultencoding( "utf-8" )

class MainWindow(QtGui.QMainWindow):
    scanemit = QtCore.pyqtSignal(str)
    anailzemit = QtCore.pyqtSignal(str) # 开始分析文件信号

    def __init__(self, parent=None):
        QtGui.QWidget.__init__(self, parent)
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        
        # checkBox对象
        # 扫描规则部分
        self.cbrall  = self.ui.CBRuleAll    # 规则全选
        self.cbryara = self.ui.CBRuleYara   # yara规则
        self.cbrclam = self.ui.CBRuleClamav # clamav
        self.cbrpeid = self.ui.CBRulePEiD   # PEiD规则
        self.cbrself = self.ui.CBRuleSelf   # 自定义规则
        self.cbrwl   = self.ui.CBRuleWL     # 白名单
        # 文件类型部分
        self.cbtall  = self.ui.CBTypeAll    # 类型全选
        self.cbtpe   = self.ui.CBTypePE     # PE类型
        self.cbtofs  = self.ui.CBTypeOffice # office类型
        self.cbtsh   = self.ui.CBTypeShell  # 脚本类型
        self.cbtzip  = self.ui.CBTypeZip    # 压缩包
        self.cbtmda  = self.ui.CBTypeMedia  # 多媒体
        self.cbtasm  = self.ui.CBTypeAsm    # asm文件

        # 设置tablewdiget属性
        # 自动适配header宽度，效果不好后期改适配最后一列
        # 设置不可编辑 设置每次选中一行
        self.table = self.ui.tableWidget
        # self.table.horizontalHeader().setResizeMode(QtGui.QHeaderView.Stretch)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setSelectionBehavior(QtGui.QAbstractItemView.SelectRows)
        self.table.setContextMenuPolicy(Qt.Qt.CustomContextMenu)
        
        # 右键菜单信号槽
        self.table.customContextMenuRequested.connect(self.generateMenu)

        self.folder   = ''
        self.dir      = ''
        self.dirsnum  = 0
        self.filenum  = 0
        self.table    = self.ui.tableWidget
        self.rowindex = 0

        self.detailwindow = detailwindow()

        # 按钮事件信号槽
        QtCore.QObject.connect(self.ui.PB_SelectFolder, QtCore.SIGNAL("clicked()"), self.selectFolder)
        QtCore.QObject.connect(self.ui.PB_Start, QtCore.SIGNAL("clicked()"), self.startScan)
        
        # checkbox信号槽
        # 使用lambda表达式
        self.cbrall.clicked.connect(lambda: self.checkBoxEvent(0))
        self.cbtall.clicked.connect(lambda: self.checkBoxEvent(1))
        self.cbryara.clicked.connect(lambda: self.checkBoxEvent(2))
        self.cbrclam.clicked.connect(lambda: self.checkBoxEvent(3)) 
        self.cbrpeid.clicked.connect(lambda: self.checkBoxEvent(4))
        self.cbrself.clicked.connect(lambda: self.checkBoxEvent(5))
        self.cbrwl.clicked.connect(lambda: self.checkBoxEvent(6))
        self.cbtpe.clicked.connect(lambda: self.checkBoxEvent(7))
        self.cbtofs.clicked.connect(lambda: self.checkBoxEvent(8))
        self.cbtsh.clicked.connect(lambda: self.checkBoxEvent(9))
        self.cbtzip.clicked.connect(lambda: self.checkBoxEvent(10))
        self.cbtmda.clicked.connect(lambda: self.checkBoxEvent(11))
        self.cbtasm.clicked.connect(lambda: self.checkBoxEvent(12))

        # 连接线程操作的信号槽
        self.scanemit.connect(self.recvInitSingal)
        self.anailzemit.connect(self.updateScanInfo)

    #假设以扫描类型作为开始扫描动作测试
    #需要实现在功能函数线程中而非UI线程
    def selectFolder(self):
        self.folder = QtGui.QFileDialog.getExistingDirectory(self, u"选择文件夹", "e:\\")#QtCore.QDir.currentPath())
        if self.folder == '':
            self.ui.statusbar.showMessage(u"操作取消")
        else:
            showmsg = u"选择：" + self.folder
            self.ui.statusbar.showMessage(showmsg)
            self.ui.lineEditScanStart.setText(self.folder)

    def startScan(self):
        self.ui.progressBar.reset()
        self.ui.statusbar.showMessage("init...")
        print "lll" + str(self.folder).decode('utf-8')
        if self.folder != '':
            self.folderThread = CheckFolder(self.folder)
            # two signals connect one slot
            self.folderThread.numberSignal.connect(self.recvInitSingal)
            self.folderThread.valueSignal.connect(self.recvInitSingal)
            #执行run方法
            self.folderThread.start()

    def recvInitSingal(self, index, msg):
        if 1 == index:
            self.dirsnum = msg
            print "folders number is: " + self.dirsnum
            self.ui.progressBar.setMaximum(int(self.filenum))
        if 2 == index:
            self.filenum = msg
            print "files number is: " + self.filenum
        if 3 == index:
            scanlist = msg
            # 扫描线程准备工作 第一版 发列表
            # 下一版可以考虑不发文件名list
            self.scanThread = ScanFile(scanlist)
            self.scanThread.fileSignal.connect(self.updateScanInfo) # 连到更新函数中
            self.scanThread.start()


    # 暂时将statusbar和tablewidget信息集中在这里
    # 验证后再分离功能
    # 可对应添加scanfile信号发射的参数
    # @msg:文件绝对路径，将分割为文件名+路径
    # @文件类型
    # @文件日期
    # @文件大小
    # @文件MD5
    # @文件SHA
    def updateScanInfo(self, num, msg, msg2):
        showmsg = 'recv result from file: ' + msg
        self.ui.statusbar.showMessage(showmsg)
        # 更新进度条 最大值和当前值放在一起
        self.ui.progressBar.setMaximum(int(self.filenum))
        self.ui.progressBar.setValue(num)

        # 更新tablewidget
        self.rowindex = self.rowindex + 1
        i = self.rowindex
        # print i
        self.table.setRowCount(i)
        # 或者用insertRow
        fsize = str(msg2[0]).decode('utf-8')
        ftype = str(msg2[1]).decode('utf-8')
        fMD5  = str(msg2[2]).decode('utf-8')
        p, f  = os.path.split(str(msg).decode('utf-8')) # 分割文件路径与文件名
        self.table.setItem(i - 1, 0, QtGui.QTableWidgetItem(f))
        self.table.setItem(i - 1, 1, QtGui.QTableWidgetItem(p))
        sizeitem = QtGui.QTableWidgetItem(fsize+"  ")
        # 设置单元内容对齐方式
        sizeitem.setTextAlignment(Qt.Qt.AlignRight|Qt.Qt.AlignVCenter)
        self.table.setItem(i - 1, 2, sizeitem)
        self.table.setItem(i - 1, 3, QtGui.QTableWidgetItem(ftype))
        self.table.setItem(i - 1, 6, QtGui.QTableWidgetItem(fMD5))
        # self.table.setItem(i - 1, 4, QtGui.QTableWidgetItem(str(msg3)))

    def updateStatusBar(self):
        pass

    def updateTableMsg(self):
        pass

    # checkbox事件
    # @flag: 标记全选与其他
    def checkBoxEvent(self, flag):
        print flag
        if flag == 0: # 对应rule全选操作
            if self.cbrall.isChecked():
                print "all rules selected"
                self.cbryara.setCheckState(Qt.Qt.Checked)
                self.cbrclam.setCheckState(Qt.Qt.Checked)
                self.cbrpeid.setCheckState(Qt.Qt.Checked)
                self.cbrself.setCheckState(Qt.Qt.Checked)
                self.cbrwl.setCheckState(Qt.Qt.Checked)
            else:
                self.cbryara.setCheckState(Qt.Qt.Unchecked)
                self.cbrclam.setCheckState(Qt.Qt.Unchecked)
                self.cbrpeid.setCheckState(Qt.Qt.Unchecked)
                self.cbrself.setCheckState(Qt.Qt.Unchecked)
                self.cbrwl.setCheckState(Qt.Qt.Unchecked)
        elif flag == 1: # 对应type全选操作
            if self.cbtall.isChecked():
                print "all type selected"
                self.cbtpe.setCheckState(Qt.Qt.Checked)
                self.cbtofs.setCheckState(Qt.Qt.Checked)
                self.cbtsh.setCheckState(Qt.Qt.Checked)
                self.cbtzip.setCheckState(Qt.Qt.Checked)
                self.cbtmda.setCheckState(Qt.Qt.Checked)
                self.cbtasm.setCheckState(Qt.Qt.Checked)
            else:
                self.cbtpe.setCheckState(Qt.Qt.Unchecked)
                self.cbtofs.setCheckState(Qt.Qt.Unchecked)
                self.cbtsh.setCheckState(Qt.Qt.Unchecked)
                self.cbtzip.setCheckState(Qt.Qt.Unchecked)
                self.cbtmda.setCheckState(Qt.Qt.Unchecked)
                self.cbtasm.setCheckState(Qt.Qt.Unchecked)
        else:
            if self.cbrall.isChecked() or self.cbtall.isChecked():
                if flag < 7:
                    self.cbrall.setCheckState(Qt.Qt.Unchecked)
                else:
                    self.cbtall.setCheckState(Qt.Qt.Unchecked)

    # 右键菜单生成函数
    def generateMenu(self, pos):
        print pos
        row_num = -1 # 右键操作列索引
        for i in self.table.selectionModel().selection().indexes():
            row_num = i.row()
        menu = QtGui.QMenu()
        item1 = menu.addAction(QtGui.QIcon(".\icons\detail_icon.png"), u"详细信息") # (u"详细信息")
        item2 = menu.addAction(QtGui.QIcon(".\icons\Fanalyz_icon.png"), u"文件分析")
        item3 = menu.addAction(QtGui.QIcon(".\icons\img_icon.png"), u"二进制图像")
        item4 = menu.addAction(QtGui.QIcon(".\icons\delete_icon.png"), u"删除文件")
        item5 = menu.addAction(QtGui.QIcon(".\icons\locate_icon.png"), u"打开文件位置")
        markmenu = menu.addMenu(QtGui.QIcon(".\icons\usermark_icon.png"), u"用户标记")
        item6 = markmenu.addAction(u"分析完成")
        item7 = markmenu.addAction(u"仍需分析")
        item8 = markmenu.addAction(u"3")
        item9 = menu.addAction(QtGui.QIcon(".\icons\upload_icon.png"), u"上传样本")
        action = menu.exec_(self.table.mapToGlobal(pos))
        if action == item1:
            print u'您选了选项一，当前行文字内容是：',self.table.item(row_num,1).text()
            filedetail = self.detailwindow
            filedetail.show()

        elif action == item2:
            print u'您选了选项二，当前行文字内容是：',self.table.item(row_num,1).text()

        elif action == item3:
            print u'您选了选项三，当前行文字内容是：',self.table.item(row_num,1).text()
        
        elif action == item7:
            print "item777"

        else:
            return


if __name__ == "__main__":

    app = QtGui.QApplication(sys.argv)
    myapp = MainWindow()
    myapp.show()

    sys.exit(app.exec_())