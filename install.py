import os
import sys
import time
import win32com.shell.shell as shell

EXT_LIST = ['avi', 'mp4', 'mkv']
MENU_LIST = [
    { 'id': 'h264 mp4 -b:v 24000k', 'label': 'h264 mp4 -b:v 24000k', 'file': 'runner.h264.24000k.mp4.py' },
]

def cur_file_dir():
    path = sys.path[0]
    if os.path.isdir(path):
        return path
    elif os.path.isfile(path):
        return os.path.dirname(path)

def uninstall():
    dp0 = cur_file_dir()

    regTexts = [
        'Windows Registry Editor Version 5.00',
        ''
    ]

    for ext in EXT_LIST:
        regTexts.append('[-HKEY_CLASSES_ROOT\SystemFileAssociations\.%s\shell\FFMpeg Converter]' % ext)
        regTexts.append('')

    open('uninstall.temporary.reg', 'w').write('\n'.join(regTexts))
    shell.ShellExecuteEx(
        lpVerb='runas',
        lpFile='reg',
        lpParameters='import "' + os.path.abspath(dp0 + '\\uninstall.temporary.reg') + '"')
    time.sleep(2)
    os.remove('uninstall.temporary.reg')

def install():
    dp0 = cur_file_dir()

    regTexts = [
        'Windows Registry Editor Version 5.00',
        ''
    ]

    for ext in EXT_LIST:
        regTexts.append('[HKEY_CLASSES_ROOT\\SystemFileAssociations\\.%s\\shell\\FFMpeg Converter]' % ext)
        regTexts.append('"MUIVerb"="FFMpeg Converter"')
        regTexts.append('"SubCommands"=""')
        regTexts.append('')
        regTexts.append('[HKEY_CLASSES_ROOT\\SystemFileAssociations\\.%s\\shell\\FFMpeg Converter\\shell]' % ext)
        regTexts.append('')

        for menu in MENU_LIST:
            regTexts.append('[HKEY_CLASSES_ROOT\\SystemFileAssociations\\.%s\\shell\\FFMpeg Converter\\shell\\%s]' % (ext, menu['id']))
            regTexts.append('"MUIVerb"="%s"' % menu['label'])
            regTexts.append('')
            regTexts.append('[HKEY_CLASSES_ROOT\\SystemFileAssociations\\.%s\\shell\\FFMpeg Converter\\shell\\%s\\command]' % (ext, menu['id']))
            regTexts.append('@="mshta vbscript:createobject(\\"shell.application\\").shellexecute(\\"python\\",\\"\\"\\"%s\\"\\" \\"\\"%%1\\"\\"\\",\\"\\",\\"open\\",1)(close)"' % os.path.abspath(dp0 + '\\' + menu['file']).replace('\\', '\\\\'))
            regTexts.append('')

    open('install.temporary.reg', 'w').write('\n'.join(regTexts))
    shell.ShellExecuteEx(
        lpVerb='runas',
        lpFile='reg',
        lpParameters='import "' + os.path.abspath(dp0 + '\\install.temporary.reg') + '"')
    time.sleep(2)
    os.remove('install.temporary.reg')

if __name__ == '__main__':
    print('Will install context menu to extensions: %s' % ','.join(EXT_LIST))
    os.system('pause')
    uninstall()

    print('Installing %s...' % ','.join(EXT_LIST))
    install()
    print('install succeed!')
    os.system('pause')
