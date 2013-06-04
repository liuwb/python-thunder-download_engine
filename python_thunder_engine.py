# -*- coding: utf-8 -*-

from ctypes import *
#Make sure XLDownload.dll and zlib1.dll are located in PATH environment variable
lib = windll.LoadLibrary("XLDownload")

from threading import Thread
import time, sys

class TaskStatus:
    Connect = 0                #已经建立连接
    Download = 2               #开始下载
    Pause = 10                 #暂停
    Success = 11               #成功下载
    Fail = 12                  #下载失败

class XLErrorCode:
    SUCCESS = 0
    FAIL = 0x10000000
    UNINITAILIZE = FAIL + 1 # 尚未进行初始化
    UNSPORTED_PROTOCOL = FAIL +2#不支持的协议，目前只支持HTTP
    INIT_TASK_TRAY_ICON_FAIL = FAIL + 3#初始化托盘图标失败
    ADD_TASK_TRAY_ICON_FAIL = FAIL + 4#添加托盘图标失败
    POINTER_IS_NULL = FAIL + 5#指针为空
    STRING_IS_EMPTY = FAIL + 6#字符串是空串
    PATH_DONT_INCLUDE_FILENAME = FAIL + 7#传入的路径没有包含文件名
    CREATE_DIRECTORY_FAIL = FAIL + 8#创建目录失败
    MEMORY_ISNT_ENOUGH = FAIL + 9#内存不足
    INVALID_ARG = FAIL + 10#参数不合法
    TASK_DONT_EXIST = FAIL + 11#任务不存在
    FILE_NAME_INVALID = FAIL + 12#文件名不合法
    NOTIMPL = FAIL + 13#没有实现
    TASKNUM_EXCEED_MAXNUM = FAIL + 14#已经创建的任务数达到最大任务数，无法继续创建任务
    INVALID_TASK_TYPE = FAIL + 15#任务类型未知
    FILE_ALREADY_EXIST = FAIL + 16#文件已经存在
    FILE_DONT_EXIST = FAIL + 17#文件不存在
    READ_CFG_FILE_FAIL = FAIL + 18#读取cfg文件失败
    WRITE_CFG_FILE_FAIL = FAIL + 19#写入cfg文件失败
    CANNOT_CONTINUE_TASK = FAIL + 20#无法继续任务，可能是不支持断点续传，也有可能是任务已经失败。通过查询任务状态，确定错误原因。
    CANNOT_PAUSE_TASK = FAIL + 21#无法暂停任务，可能是不支持断点续传，也有可能是任务已经失败。通过查询任务状态，确定错误原因。
    BUFFER_TOO_SMALL = FAIL + 22#缓冲区太小
    INIT_THREAD_EXIT_TOO_EARLY = FAIL + 23#调用XLInitDownloadEngine的线程，在调用XLUninitDownloadEngine之前已经结束。初始化下载引擎线程，在调用XLUninitDownloadEngine之前，必须保持执行状态。
    TP_CRASH = FAIL + 24#TP崩溃
    TASK_INVALID = FAIL + 25#任务不合法，调用XLContinueTaskFromTdFile继续任务。内部任务切换失败时，会产生这个错误。


def engine_init():
    return lib.XLInitDownloadEngine() != 0

def engine_exit():
    return lib.XLUninitDownloadEngine() != 0

def engine_new_download_task(saved_file_path, url, refUrl = None):
    taskId = c_ulong(0)
    errorId = lib.XLURLDownloadToFile(c_wchar_p(saved_file_path), c_wchar_p(url), c_wchar_p(refUrl), byref(taskId))
    return errorId, int(taskId.value)

#同步调用
def sync_engine_download_task(saved_file_path, url, refUrl = None, download_progress_callback = None,
                        download_success_callback = None, download_error_callback = None):
    errorId,taskId = engine_new_download_task(saved_file_path, url, refUrl)
    if errorId != XLErrorCode.SUCCESS:
        if download_error_callback:
            download_error_callback(url)
        return False, errorId
    return polling_for_task(taskId, url, download_progress_callback, download_success_callback, download_error_callback)


def polling_for_task(taskId, url, download_progress_callback = None,
                        download_success_callback = None, download_error_callback = None):
    while True:
        time.sleep(1)
        errorId,status,fileSize,recvSize = engine_query_task_info(taskId)
        if errorId != XLErrorCode.SUCCESS:
            if download_error_callback:
                download_error_callback(url)
            engine_stop_task(taskId)
            return False, errorId

        if status == TaskStatus.Connect or status == TaskStatus.Pause:
            pass
        elif status == TaskStatus.Download:
            if download_progress_callback:
                download_progress_callback(url, recvSize, fileSize)
        elif status == TaskStatus.Success:
            engine_stop_task(taskId)
            if download_success_callback:
                download_success_callback(url, fileSize)
            return True, None
        else:#error
            if download_error_callback:
                download_error_callback(url)
            break
    engine_stop_task(taskId)
    return False, None


#异步调用
def async_engine_download_task(saved_file_path, url, refUrl = None, download_progress_callback = None,
                        download_success_callback = None, download_error_callback = None):
    errorId,taskId = engine_new_download_task(saved_file_path, url, refUrl)
    if errorId != XLErrorCode.SUCCESS:
        if download_error_callback:
            download_error_callback(url)
        return False, errorId
    thread = Thread(target = polling_for_task,
                    args = (taskId, download_progress_callback,
                            download_success_callback, download_error_callback)
                    )
    thread.start()
    return True, None


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

    saved_file_path = r"d:\temp\my.xv"
    url = "http://pubnet.sandai.net:8080/20/7ef17476e08edc8887c7b216a88895204da2c325/c8fa4ecfa6b3d9555ad53bf84d56a2d7782d221e/e849084/200000/0/4b2ea/0/0/e849084/0/index=0-25754/indexmd5=f571e87c41db4619ad6fa08dc0b69024/10279ecbc2c3d3c1487eb2c6b05311e7/b4190fa019332065d0589f86cce3a8b3/c8fa4ecfa6b3d9555ad53bf84d56a2d7782d221e_1.flv.xv?type=vod&movieid=166852&subid=439810&ext=.xv"
    def progress_cb(url, recvSize, fileSize):
        if fileSize > 0:
            progress = float(recvSize) / float(fileSize)
            progressbar(progress, "Downloading: ")
    def success_cb(url, fileSize):
        sys.stdout.write("\nDownloaded successfully, fileSize:%d\n" % fileSize)
        sys.stdout.flush()
    def error_cb(url):
        sys.stdout.write("\nFailed to download\n")
        sys.stdout.flush()

    success, errorId = sync_engine_download_task(saved_file_path, url, refUrl = None,
                        download_progress_callback = progress_cb,
                        download_success_callback = success_cb,
                        download_error_callback = error_cb)
    if not success and errorId:
        print engine_get_error_msg(errorId)
    engine_exit()
