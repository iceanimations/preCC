'''
Created on Aug 12, 2015

@author: qurban.ali
'''
import sys
import os
if os.environ['USERNAME'] == 'qurban.ali':
    sys.path.insert(0, 'D:/My/Tasks/workSpace')
else:
    sys.path.insert(0, 'R:/Python_Scripts/plugins')

import sip
sip.setapi('QString', 2)
from PyQt4.QtGui import QApplication, QStyleFactory
import sys
import _compositing as comp


if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyle(QStyleFactory.create('plastique'))
    global win
    win = comp.Compositor()
    win.show()
    sys.exit(app.exec_())