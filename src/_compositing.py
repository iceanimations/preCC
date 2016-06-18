'''
Created on Aug 12, 2015

@author: qurban.ali
'''
from site import addsitedir as asd
asd(r'R:\Pipe_Repo\Users\Qurban\utilities')
asd(r"R:\Pipe_Repo\Projects\TACTIC")
from PyQt4 import uic
from PyQt4.QtGui import QMessageBox, QFileDialog, qApp
import os.path as osp
import msgBox
import os
import re
import cui
reload(cui)
import shutil
import appUsageApp
import subprocess
import sys
import pprint
import iutil
import time

reload(iutil)

title = 'PreCC'

homeDir = osp.join(osp.expanduser('~'), 'preCC')
if not osp.exists(homeDir):
    os.mkdir(homeDir)

rootPath = iutil.dirname(__file__, depth=2)
uiPath = osp.join(rootPath, 'ui')
iconPath = osp.join(rootPath, 'icons')
renderShotBackend = 'R:\\Python_Scripts\\plugins\\renderShots\\src\\backend'
if os.environ['USERNAME'] == 'qurban.ali':
    renderShotBackend = 'D:\\My\\Tasks\\workSpace\\renderShots\\src\\backend'
sys.path.insert(0, renderShotBackend)
compositingFie = osp.join(renderShotBackend, 'compositing.py')

nukePath = r'C:\Program Files\Nuke8.0v5'
if not osp.exists(nukePath):
    nukePath = r'C:\Program Files\Nuke9.0v4'
    
compositingInfo = osp.join(osp.expanduser('~'), 'compositing')
if not osp.exists(compositingInfo):
    os.mkdir(compositingInfo)
    
def executeCommand(command):
    pass

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
            t1 = time.time()
            self.startButton.setEnabled(False)
            for directory in os.listdir(homeDir):
                path = osp.join(homeDir, directory)
                if osp.isdir(path):
                    shutil.rmtree(path, onerror=iutil.onerror)
    
            shots = self.shotsBox.getSelectedItems()
            if not shots:
                shots = self.shotsBox.getItems()
            if shots:
                self.progressBar.show()
                if self.isMoveFile():
                    pass
                else:
                    frames = self.copyRenders(shots)
                self.progressBar.setValue(0)
                qApp.processEvents()
    
                self.setStatus('Creating and rendering comps')
                compDir = osp.join(homeDir, 'comps')
                if not osp.exists(compDir):
                    os.mkdir(compDir)
                temp = False
                if self.isMoveFile():
                    temp = self.getShotsPath(msg=False)
                with open(osp.join(compositingInfo, 'info.txt'), 'w') as f:
                    f.write(str([temp, homeDir] + shots))
                
                # create the comps and render them
                subprocess.call('\"' + osp.join(nukePath, 'python') + '\" ' + compositingFie, shell=True)
    
                renderPath = osp.join(compDir, 'renders')
                tt = time.time()
                with open(osp.join(osp.expanduser('~'), 'compositing', 'errors.txt')) as f:
                    errors = eval(f.read())
                    if errors:
                        btn = self.showMessage(msg='Errors occurred while creating and rendering comps',
                                               ques='Do you want to continue?',
                                               icon=QMessageBox.Critical,
                                               details=iutil.dictionaryToDetails(errors),
                                               btns=QMessageBox.Yes|QMessageBox.No)
                        if btn == QMessageBox.No:
                            return
                ttt = time.time() - tt
                if self.isMoveFile():
                    # add black frames for missing frames
                    self.setStatus('Finding missing frames')
                    for i, shot in enumerate(shots):
                        self.setSubStatus('Finding for %s (%s of %s)'%(shot, i+1, len(shots)))
                        shotPath = osp.join(renderPath, shot)
                        if not osp.exists(shotPath): continue
                        files = os.listdir(shotPath)
                        if not files: continue
                        fn = set([int(x.split('.')[1]) for x in files]) # frame numbers
                        mf = list(set(range(min(fn), max(fn) + 1)).difference(fn)) # missing frames
                        if not mf: continue
                        bip = osp.join(shotPath, 'black.jpg')
                        imgSize = None
                        for ph in files:
                            imgSize = iutil.get_image_size(osp.join(shotPath, ph))
                            if not imgSize: continue
                            else: break
                        if not imgSize: continue
                        for j in mf:
                            shutil.copy(r"R:\Pipe_Repo\Users\Qurban\extras\black.jpg", shotPath)
                            newName = osp.join(shotPath, files[0].split('.')[0] +'.'+ str(j).zfill(5) + '.jpg')
                            os.rename(bip, newName)
                            if imgSize != (1920, 1080):
                                iutil.resizeImage(newName, str(str(imgSize[0])) +'x'+ str(imgSize[1]))
                    self.setStatus('Adding shot and frame numbers to the renders')
                    self.addShotNumbers(renderPath, shots)
                    allRendersPath = osp.join(osp.join(renderPath, 'all'))
                    if not osp.exists(allRendersPath):
                        os.mkdir(allRendersPath)
                    movPath, overlaping = self.createMovFile(allRendersPath)
                    totalTime = int(time.time() - (t1 + ttt))
                    if overlaping:
                        self.showMessage(msg='Some errors occurred while creating .mov file, it might be due to overlaping frames',
                                         details=qutil.dictionaryToDetails(overlaping),
                                         icon=QMessageBox.Information)
                    if osp.exists(movPath):
                        arg = '<b>%s</b> Second(s)'%str(totalTime)
                        if totalTime > 60:
                            arg = '<b>%s</b> Minute(s) <b>%s</b> Second(s)'%(str(totalTime/60), str(totalTime%60))
                        movPath = movPath.replace('\\', '/')
                        self.showMessage(msg='<a href=\"%s\">%s</a><br>%s'%(movPath, movPath, 'Total Time: %s'%arg))
                    else:
                        self.showMessage(msg='Could not create .mov file', icon=QMessageBox.Critical)
                else:
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
                        if frames.has_key(shot):
                            cMaker.makeShot(shot, size=str(self.sizeBox.value())+'%', text=frames[shot])
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
            self.startButton.setEnabled(True)
            
    def addShotNumbers(self, renderPath, shots):
        shotLen = len(shots)
        for i, shot in enumerate(shots):
            self.setSubStatus('Adding to %s (%s of %s)'%(shot, i+1, shotLen))
            shotPath = osp.join(renderPath, shot)
            if not osp.exists(shotPath): continue
            try: files = os.listdir(shotPath)
            except: continue
            self.progressBar.setValue(0)
            self.progressBar.setMaximum(len(files))
            for j, ph in enumerate(files):
                try: sh, frame, _ = ph.split('.')
                except: continue
                filePath = osp.normpath(osp.join(shotPath, ph))
                text = sh + '[' + frame + ']'
                command = "\"C:\\Program Files\\ImageMagick-6.9.1-Q8\\convert.exe\""
                if not osp.exists(command.strip("\"")):
                    command = 'R:\\Pipe_Repo\\Users\\Qurban\\applications\\ImageMagick\\convert.exe'
                command += ' %s -pointsize 30 -channel RGBA -fill black -stroke white -draw "text 20,55 %s" %s'%(filePath, text, filePath)
                subprocess.call(command, shell=True)
                self.progressBar.setValue(j+1)
                qApp.processEvents()
        self.setStatus('')
        self.setSubStatus('')
        self.progressBar.setValue(0)
                

    def isMoveFile(self):
        return self.createMovButton.isChecked()
    
    def createMovFile(self, allRendersPath):
        overlaping = {}
        rendersPath = osp.dirname(allRendersPath)
        shots = os.listdir(rendersPath)
        shots.remove('all')
        seqName = osp.basename(self.getShotsPath())
        self.setStatus('Preparing to create .mov file')
        ln = len(shots)
        self.progressBar.setMaximum(ln)
        self.progressBar.setValue(0)
        for i, shot in enumerate(shots):
            self.setSubStatus('Processing %s (%s of %s)'%(shot, i+1, ln))
            shotPath = osp.join(rendersPath, shot)
            files = os.listdir(shotPath)
            for ph in files:
                shutil.copy(osp.join(shotPath, ph), allRendersPath)
                try:
                    os.rename(osp.join(allRendersPath, ph), osp.join(allRendersPath, re.sub('SH\d+\.', seqName+'.', ph)))
                except Exception as ex:
                    overlaping[ph] = (str(ex))
                    os.remove(osp.join(allRendersPath, ph))
            self.progressBar.setValue(i+1)
            qApp.processEvents()
        self.progressBar.setValue(0)
        files = sorted(os.listdir(allRendersPath))
        ln = len(files)
        for i, ph in enumerate(files):
            phNewName = re.sub('\.\d+\.', '.'+ str(i).zfill(5) +'.', ph)
            self.setSubStatus('Renaming file: %s -> %s (%s of %s)'%(ph, phNewName, i+1, ln))
            os.rename(osp.join(allRendersPath, ph), osp.join(allRendersPath, phNewName))
        movName = seqName+'.mov'
        movPath = osp.join(allRendersPath, movName)
        tempPath = osp.join(allRendersPath, seqName)
        self.setSubStatus('Creating %s'%osp.basename(movPath))
        subprocess.call("R:\\Pipe_Repo\\Users\\Qurban\\applications\\ffmpeg\\bin\\ffmpeg.exe -i "+ tempPath + ".%05d.jpg -c:v prores -r 25 -pix_fmt yuv420p "+ movPath, shell=True)
        self.setStatus('')
        self.setSubStatus('')
        return movPath, overlaping
        
    def copyRenders(self, shots):
        shotsDir = self.getShotsPath()
        numShots = len(shots)
        self.progressBar.setMaximum(numShots)
        self.progressBar.setValue(0)
        frames = {}
        for i, shot in enumerate(shots):
            numFrames = 0
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
                if osp.isfile(layerDir): continue
                for aov in os.listdir(layerDir):
                    if aov.lower().endswith('beauty'):
                        aovDirLocal = osp.join(layerDirLocal, aov)
                        if not osp.exists(aovDirLocal):
                            os.mkdir(aovDirLocal)
                        aovDir = osp.join(layerDir, aov)
                        if osp.isfile(aovDir): continue
                        renders = os.listdir(aovDir)
                        if renders:
                            goodRenders = list(self.getGoodFiles(renders))
                            if self.isMoveFile():
                                goodRenders = renders
                            if len(goodRenders) > 1:
                                frameRange = [int(re.search('\.\d+\.', phile).group()[1:-1]) for phile in goodRenders]
                                minFrame = min(frameRange); maxFrame = max(frameRange)
                                nf = maxFrame - minFrame
                                if nf > numFrames:
                                    numFrames = nf
                                    frames[shot] = frameRange
                            for phile in goodRenders:
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
        return frames
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
                                                    QFileDialog.ShowDirsOnly | QFileDialog.DontUseNativeDialog)
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
        return osp.normpath(path) if path else path
    
    def populateShots(self):
        path = self.getShotsPath(msg=False)
        if path:
            shots = [shot for shot in os.listdir(path)]
            self.shotsBox.addItems(shots)
    
    def closeEvent(self, event):
        self.deleteLater()
        event.accept()