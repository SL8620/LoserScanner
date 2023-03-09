import cv2 as cv
import sys
import numpy as np
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtGui import *
from PyQt5.QtWidgets import QFileDialog, QMainWindow
from scanner import Ui_MainWindow
from PyQt5.QtCore import Qt


# QT窗口类
class PyQtMainEntry(QMainWindow, Ui_MainWindow):
    def __init__(self):
        super().__init__()  # 我也不知道这是干啥的
        self.setupUi(self)  # 建立对象
        self.picPath = None  # 图片路径在哪里
        self.picSize = []  # 图片参数，0-rows，1-columns，2-channels
        self.box = [0, 0, 0, 0]  # 存放自己选的四个边框点（其实3个就够，为什么扫描王要四个）
        self.boxList = [0, 0, 0, 0]  # 和楼上存一样的东西，后期转numpy对象用到
        self.mouseWindowName = 'BoxPick'  # 选边框的窗口名，不要轻易删
        self.img = None  # 原图像
        self.boxedImg = None  # 显示裁剪范围的图像
        self.resultImg = None  # 处理结果

    def pickPic_clicked(self):
        # 打开文件选取对话框
        filename, _ = QFileDialog.getOpenFileName(self, '打开图片')  # 下划线是不关心返回值类型的意思
        if filename:  # 读取到了图像
            self.picPath = filename  # 路径赋值
            self.img = cv.imread(self.picPath)  # 使用cv读取
            self.boxedImg = self.img.copy()  # 忘了当初为啥要用boxedImg来显示了
            self.boxedImg = cv.cvtColor(self.boxedImg, cv.COLOR_BGR2RGB)  # OpenCV图像以BGR通道存储，显示时需要从BGR转到RGB
            self.picSize = self.boxedImg.shape  # 获取图像大小等信息
            rows, cols, channels = self.boxedImg.shape  # 重复了，怎么写的，脑袋坏了吗
            bytesPerLine = channels * cols
            QImg = QImage(self.boxedImg.data, cols, rows, bytesPerLine, QImage.Format_RGB888)
            # 在UI界面rawPic显示原始图片
            self.rawPic.setPixmap(
                QPixmap.fromImage(QImg).scaled(self.rawPic.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation))

    def on_mouse(self, event, x, y, flags, param):
        # 监听鼠标事件
        if event == cv.EVENT_LBUTTONDOWN:  # 别看这种写法比较冗余，但这是手残党的福音，谁也没办法确定一次就能选好那个点
            if x < self.picSize[1] / 2 and y < self.picSize[0] / 2:  # 左上
                self.box[0] = (x, y)
                self.boxList[0] = [x, y]
            elif x < self.picSize[1] / 2 and y > self.picSize[0] / 2:  # 左下
                self.box[1] = (x, y)
                self.boxList[1] = [x, y]
            elif x > self.picSize[1] / 2 and y < self.picSize[0] / 2:  # 右上
                self.box[2] = (x, y)
                self.boxList[2] = [x, y]
            elif x > self.picSize[1] / 2 and y > self.picSize[0] / 2:  # 右下
                self.box[3] = (x, y)
                self.boxList[3] = [x, y]

            # print(self.box)

            img_circle = self.img.copy()
            # 画圆
            for pos in self.box:
                if pos != 0:
                    cv.circle(img_circle, pos, 10, (0, 255, 0), thickness=3)
            # 划线
            img_line = img_circle.copy()
            if (self.box[0] != 0 and self.box[2] != 0):
                cv.line(img_line, self.box[0], self.box[2], (0, 0, 255), thickness=5)
            if (self.box[0] != 0 and self.box[1] != 0):
                cv.line(img_line, self.box[0], self.box[1], (0, 0, 255), thickness=5)
            if (self.box[2] != 0 and self.box[3] != 0):
                cv.line(img_line, self.box[2], self.box[3], (0, 0, 255), thickness=5)
            if (self.box[1] != 0 and self.box[3] != 0):
                cv.line(img_line, self.box[1], self.box[3], (0, 0, 255), thickness=5)
            # 显示框选后或选点后的图像
            cv.imshow(self.mouseWindowName, img_line)
            # 下面是在boxedPic一览显示框选后图像的，这样的代码算上刚才的被编译器提示一共有三段重复，编译器都在嘲讽我，能封装还是封装一下吧
            self.boxedImg = cv.cvtColor(img_line, cv.COLOR_BGR2RGB)  # OpenCV图像以BGR通道存储，显示时需要从BGR转到RGB
            self.picSize = self.boxedImg.shape
            # print(self.picSize)
            rows, cols, channels = self.boxedImg.shape
            bytesPerLine = channels * cols
            QImg = QImage(self.boxedImg.data, cols, rows, bytesPerLine, QImage.Format_RGB888)
            self.boxedPic.setPixmap(
                QPixmap.fromImage(QImg).scaled(self.boxedPic.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation))

    def pickBox_clicked(self):  # 点了选择边框之后会发生的事
        if self.picPath:
            cv.namedWindow(self.mouseWindowName)  # 先创建一个窗口
            cv.setMouseCallback(self.mouseWindowName, self.on_mouse)  # 开始监听鼠标事件
            cv.imshow(self.mouseWindowName, self.img)  # 在这上面首次显示初始图片，会被后续的覆盖掉
            cv.waitKey(0)  # 点x才能退出

    def resultPic_clicked(self):  # 点了处理图片后会发生的事
        imgbak = np.array(self.img)  # 先转化成numpy里的array
        destPoint = [(0, 0), (0, self.picSize[0]), (self.picSize[1], self.picSize[0])]  # 新图片目标点，大小和原图片是一样的
        pointList = [self.boxList[0], self.boxList[1], self.boxList[3]]  # 原图片目标点，要与楼上对应，这里选的是左上左下右下三点
        pts1 = np.float32(pointList)  # 听说转成float更好处理？
        pts2 = np.float32(destPoint)
        M = cv.getAffineTransform(pts1, pts2)  # 本项目最核心的一句话，计算仿射变换矩阵
        dst = cv.warpAffine(imgbak, M, (self.picSize[1], self.picSize[0]))  # 将仿射变换矩阵应用到原图像，生成目标图像
        self.resultImg = dst.copy()  # 保存一下

        Img = cv.cvtColor(dst, cv.COLOR_BGR2RGB)  # OpenCV图像以BGR通道存储，显示时需要从BGR转到RGB
        rows, cols, channels = Img.shape
        bytesPerLine = channels * cols
        QImg = QImage(Img.data, cols, rows, bytesPerLine, QImage.Format_RGB888)
        self.outPic.setPixmap(
            QPixmap.fromImage(QImg).scaled(self.outPic.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation))

    def savePic_clicked(self):  # 点了保存图像之后会发生的事
        cv.imwrite('afterPic.png', self.resultImg)


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = PyQtMainEntry()
    window.show()
    sys.exit(app.exec_())
