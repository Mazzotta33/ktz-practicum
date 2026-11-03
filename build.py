"""Build a standalone Windows executable using project-local build dependencies."""
from pathlib import Path
import sys
import shutil

root=Path(__file__).resolve().parent
sys.path.insert(0,str(root/'.build-deps'))

def main():
    from PIL import Image, ImageDraw
    icon=Image.new('RGBA',(256,256),'#12233c')
    draw=ImageDraw.Draw(icon)
    for i in range(3):
        for j in range(3):
            x,y=40+j*60,40+i*60
            draw.rounded_rectangle((x,y,x+50,y+50),radius=9,fill='#49c5ad' if i==j else '#315fea')
    draw.line((58,180,118,120,180,58),fill='white',width=10)
    icon.save(root/'icon.ico',sizes=[(16,16),(32,32),(48,48),(64,64),(128,128),(256,256)])
    import PyInstaller.__main__
    PyInstaller.__main__.run([
        '--noconfirm','--clean','--onefile','--windowed','--name','KTZ-Practicum',
        '--icon',str(root/'icon.ico'),'--add-data',str(root/'icon.ico')+';.',
        '--distpath',str(root/'dist'),'--workpath',str(root/'.build'),
        '--specpath',str(root),str(root/'app.py')])
    destination=root.parent/'КТЗ-Практикум.exe'
    shutil.copy2(root/'dist'/'KTZ-Practicum.exe',destination)
    print('Built:',destination)


if __name__=='__main__':main()
