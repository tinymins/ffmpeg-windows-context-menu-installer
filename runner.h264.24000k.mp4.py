from sys import argv
import os

if __name__ == '__main__':
    os.system('@color 0A & title FFMpeg Converter to h264 mp4 24000k')
    bDirectVisit = False if argv[1:] else True
    while True:
        while not argv[1:]:
            print('Input original video file path:')
            sfn = input('')
            sfn = sfn.replace("\"", "")
            if sfn != 0:
                if os.path.exists(sfn):
                    argv.append(sfn)
                    print('====================')
        sfn = argv[1].replace("\"", "")
        del argv[1]
        sShellString = (
            'ffmpeg.exe -i'
            ' "%s"'
            ' -c:v libx264'
            ' -x264-params "profile=high:level=3.0" -preset ultrafast'
            ' -b:v 24000k -bufsize 64000k'
            ' "%s.h264.mp4"'
        ) % (sfn, sfn[0:sfn.rfind(".")])
        sLampDir = os.path.dirname(__file__)
        os.system(
            'cmd.exe /c '
            + ' @echo off '
            + ' & title FFMpeg Converter to h264 mp4 24000k'
            + ' & color 0A '
            + ' & cd "'+sLampDir+'"'
            + ' & '+sLampDir[0:1]+':'
            + ' & echo # '+sfn[sfn.rfind("\\")+1:]+':'
            + ' & echo ==============================================='
            + ' & '+sShellString
            + ' & echo ================================================'
        )
        print('')
        if not bDirectVisit and not argv[1:]:
            os.system('pause')
            break
