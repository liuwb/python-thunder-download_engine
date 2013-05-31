# -*- coding: utf-8 -*-

from ctypes import *
#Make sure XLDownload.dll and zlib1.dll are located in PATH environment variable
lib = windll.LoadLibrary("XLDownload")

class TaskStatus:
    Connect = 0                #已经建立连接
    Download = 2               #开始下载
    Pause = 10                 #暂停
    Success = 11               #成功下载
    Fail = 12                  #下载失败


def engine_init():
    return lib.XLInitDownloadEngine() != 0

def engine_exit():
    return lib.XLUninitDownloadEngine() != 0

def engine_new_download_task(saved_file_path, url, refUrl = None):
    taskId = c_ulong(0)
    errorId = lib.XLURLDownloadToFile(c_wchar_p(saved_file_path), c_wchar_p(url), c_wchar_p(refUrl), byref(taskId))
    return errorId, int(taskId.value)

def engine_query_task_info(taskId):
    status = c_long()
    fileSize = c_ulonglong()
    recvSize = c_ulonglong()
    errorId = lib.XLQueryTaskInfo(taskId, byref(status), byref(fileSize), byref(recvSize))

    return errorId, int(status.value), long(fileSize.value), long(recvSize.value)

def engine_pause_task(taskId):
    newTaskId = c_long()
    errorId = lib.XLPauseTask(taskId, byref(newTaskId))
    return errorId, int(newTaskId.value)

def engine_continue_task(taskId):
    errorId = lib.XLContinueTask(taskId);
    return errorId

def engine_continue_task_from_td_file(tdFilePath):
    taskId = c_long()
    errorId = lib.XLContinueTaskFromTdFile(c_wchar_p(tdFilePath), byref(taskId))
    return errorId, int(taskId.value)

def engine_stop_task(taskId):
    errorId = lib.XLStopTask(taskId)
    return errorId

def engine_get_error_msg(errorId):
    buffer = create_unicode_buffer('\000' * 32)
    bufferSize = c_ulong(32)
    success = lib.XLGetErrorMsg(errorId, buffer, byref(bufferSize))
    if success != 0:
        buffer = create_unicode_buffer('\000' * int(bufferSize.value))
        lib.XLGetErrorMsg(errorId, buffer, byref(bufferSize))
    return repr(buffer.value)



def progressbar(progress, prefix = "", size = 30):
    x = int(size*progress)
    sys.stdout.write("\r%s[%s%s] %.2f%%" % (prefix, "#"*x, "."*(size-x), progress*100.0))
    sys.stdout.flush()

if __name__ == '__main__':
    success = engine_init()
    if not success:
        print "unable to init engine"
        quit()
    saved_file_path = r"d:\temp\my1.xv"
    url = "http://pubnet.sandai.net:8080/20/7ef17476e08edc8887c7b216a88895204da2c325/c8fa4ecfa6b3d9555ad53bf84d56a2d7782d221e/e849084/200000/0/4b2ea/0/0/e849084/0/index=0-25754/indexmd5=f571e87c41db4619ad6fa08dc0b69024/10279ecbc2c3d3c1487eb2c6b05311e7/b4190fa019332065d0589f86cce3a8b3/c8fa4ecfa6b3d9555ad53bf84d56a2d7782d221e_1.flv.xv?type=vod&movieid=166852&subid=439810&ext=.xv"
    errorId,taskId = engine_new_download_task(saved_file_path, url)
    if errorId != 0:
        print engine_get_error_msg(errorId)
        engine_exit()
        quit()
    while True:
        import time
        import sys
        time.sleep(1)
        errorId,status,fileSize,recvSize = engine_query_task_info(taskId)
        if errorId != 0:
            print engine_get_error_msg(errorId)
            engine_exit()
            quit()

        if fileSize > 0:
            progress = float(recvSize) / float(fileSize)
            progressbar(progress, "Downloading: ")
        if status == TaskStatus.Connect:
            sys.stdout.write("\rConnections established")
        elif status == TaskStatus.Download:
            pass
        elif status == TaskStatus.Pause:
            sys.stdout.write("\rPaused")
        elif status == TaskStatus.Success:
            sys.stdout.write("Downloaded successfully\n")
            break
        elif status == TaskStatus.Fail:
            sys.stdout.write("Failed to download\n")
            break
        else:
            sys.stdout.write("Unknown error\n")
            break
        sys.stdout.flush()
    sys.stdout.flush()
    engine_stop_task(taskId)
    engine_exit()