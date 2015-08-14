'''
Created on Aug 12, 2015

@author: qurban.ali
'''
from site import addsitedir as asd
asd(r'R:\Pipe_Repo\Users\Qurban\utilities')
from PyQt4 import uic
from PyQt4.QtGui import QMessageBox, QFileDialog, qApp
import os.path as osp
import msgBox
import qutil
reload(qutil)
import os
import re
import cui
reload(cui)
import shutil
import appUsageApp
import subprocess
import sys
import os

title = 'PreCC'

homeDir = osp.join(osp.expanduser('~'), 'preCC')
if not osp.exists(homeDir):
    os.mkdir(homeDir)

rootPath = qutil.dirname(__file__, depth=2)
uiPath = osp.join(rootPath, 'ui')
iconPath = osp.join(rootPath, 'icons')
renderShotBackend = osp.join('R:', 'Python_Scripts', 'plugins', 'renderShots', 'src', 'backend')
sys.path.insert(0, renderShotBackend)
compositingFie = osp.join(renderShotBackend, 'compositing.py')

nukePath = r'C:\Program Files\Nuke8.0v5'
if not osp.exists(nukePath):
    nukePath = r'C:\Program Files\Nuke9.0v4'
    
compositingInfo = osp.join(osp.expanduser('~'), 'compositing')
if not osp.exists(compositingInfo):
    os.mkdir(compositingInfo)

Form, Base = uic.loadUiType(osp.join(uiPath, 'main.ui'))
class Compositor(Form, Base):
    '''
    Takes input from the user to create comp and collage
    '''
    def __init__(self, parent=None, data=None):
        super(Compositor, self).__init__(parent)
        self.setupUi(self)
        
        self.setWindowTitle(title)
        self.shotsBox = cui.MultiSelectComboBox(self, '--Select Shots--')
        self.pathLayout.addWidget(self.shotsBox)
        
        self.lastPath = ''
        
        self.startButton.clicked.connect(self.start)
        self.browseButton.clicked.connect(self.setPath)
        self.shotsPathBox.textChanged.connect(self.populateShots)
        
        if not osp.exists(nukePath):
            self.showMessage(msg='It seems like Nuke is not installed, can not create comp')
            return
        self.progressBar.hide()
        
        appUsageApp.updateDatabase('PreCC')
        
    def start(self):
        try:
            for directory in os.listdir(homeDir):
                path = osp.join(homeDir, directory)
                if osp.isdir(path):
                    shutil.rmtree(path)
        
            shots = self.shotsBox.getSelectedItems()
            if not shots:
                shots = self.shotsBox.getItems()
            if shots:
                self.progressBar.show()
                self.copyRenders(shots)
                self.progressBar.setValue(0)
                qApp.processEvents()
                
                self.setStatus('Creating and rendering comps...')
                compDir = osp.join(homeDir, 'comps')
                if not osp.exists(compDir):
                    os.mkdir(compDir)
                with open(osp.join(compositingInfo, 'info.txt'), 'w') as f:
                    f.write(str([homeDir] + shots))
                
                # create the comps and render them
                os.chdir(nukePath)
                subprocess.call('python '+ compositingFie + ' '+ homeDir + ' '+' '.join(shots), shell=True)
                
                # create collage
                self.setStatus('Creating collage')
                import collageMaker as cm
                reload(cm)
                cm.homeDir = homeDir
                cm.compRenderDir = osp.join(homeDir, 'comps', 'renders')
                cm.collageDir = osp.join(homeDir, 'collage')
                if not osp.exists(cm.collageDir):
                    os.mkdir(cm.collageDir)
                
                cMaker = cm.CollageMaker()
                numShots = len(shots)
                for i, shot in enumerate(shots):
                    self.setSubStatus('Creating %s (%s of %s)'%(shot, i+1, numShots))
                    cMaker.makeShot(shot, size=str(self.sizeBox.value())+'%')
                    self.progressBar.setValue(i+1)
                    qApp.processEvents()
                collagePath = cMaker.make().replace('\\', '/')
                self.showMessage(msg='<a href=\"%s\">%s</a>'%(collagePath, collagePath))
        except Exception as ex:
            self.showMessage(msg=str(ex),
                             icon=QMessageBox.Critical)
            
        finally:
            self.progressBar.hide()
            self.setStatus('')
            self.setSubStatus('')
        
    def copyRenders(self, shots):
        shotsDir = self.getShotsPath()
        numShots = len(shots)
        self.progressBar.setMaximum(numShots)
        for i, shot in enumerate(shots):
            self.setStatus('Scaning %s (%s of %s)'%(shot, i+1, numShots))
            shotDirLocal = osp.join(homeDir, shot)
            if not osp.exists(shotDirLocal):
                os.mkdir(shotDirLocal)
            shotDir = osp.join(shotsDir, shot)
            cameraDir = osp.join(shotDir, os.listdir(shotDir)[0])
            layers = os.listdir(cameraDir)
            numLayers = len(layers)
            for k, layer in enumerate(layers):
                self.setSubStatus('Scaning %s (%s of %s)'%(layer, k+1, numLayers))
                layerDirLocal = osp.join(shotDirLocal, layer)
                if not osp.exists(layerDirLocal):
                    os.mkdir(layerDirLocal)
                layerDir = osp.join(cameraDir, layer)
                for aov in os.listdir(layerDir):
                    if aov.lower().endswith('beauty'):
                        aovDirLocal = osp.join(layerDirLocal, aov)
                        if not osp.exists(aovDirLocal):
                            os.mkdir(aovDirLocal)
                        aovDir = osp.join(layerDir, aov)
                        renders = os.listdir(aovDir)
                        if renders:
                            for phile in self.getGoodFiles(renders):
                                shutil.copy(osp.join(aovDir, phile), aovDirLocal)
                            num = len(os.listdir(aovDirLocal))
                            if num < 3:
                                frame = re.search('\.\d+\.', phile).group()[1:-1]
                                frameLength = len(frame)
                                frameInt = int(frame)
                                for j in range(frameInt+1, frameInt+(4-num)):
                                    shutil.copyfile(osp.join(aovDirLocal, phile), osp.join(aovDirLocal, re.sub('\.\d+\.', '.'+ str(j).zfill(frameLength) +'.', phile)))
                self.progressBar.setValue(i+1)
                qApp.processEvents()
        self.setStatus('')
        self.setSubStatus('')
    def getGoodFiles(self, renders):
        mid = int(len(renders)/2)
        if len(renders) % 2 != 0:
            mid -= 1
        renders = sorted(renders)
        yield renders[0]
        for i, phile in enumerate(renders):
            if i+1 == mid:
                yield phile
                break
        yield renders[-1]
        
    def setStatus(self, msg):
        self.statusLabel.setText(msg)
        qApp.processEvents()

    def setSubStatus(self, msg):
        self.subStatusLabel.setText(msg)
        qApp.processEvents()
    
    def setPath(self):
        filename = QFileDialog.getExistingDirectory(self, title, self.lastPath,
                                                    QFileDialog.ShowDirsOnly)
        if filename:
            self.lastPath = filename
            self.shotsPathBox.setText(filename)

    def showMessage(self, **kwargs):
        return cui.showMessage(self, title=title, **kwargs)
            
    def getShotsPath(self, msg=True):
        path = self.shotsPathBox.text()
        if (not path or not osp.exists(path)) and msg:
            self.showMessage(msg='The system could not find the path specified',
                             icon=QMessageBox.Information)
            path = ''
        return path
    
    def populateShots(self):
        path = self.getShotsPath(msg=False)
        if path:
            shots = [shot for shot in os.listdir(path)]
            self.shotsBox.addItems(shots)
    
    def closeEvent(self, event):
        self.deleteLater()
        event.accept()