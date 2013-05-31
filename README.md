python-thunder-download_engine
==============================

The python binding for thunder download engine: http://xldoc.xl7.xunlei.com/0000000026/index.html

Since we are using ctypes module, and the thunder download engine is built as 64bit dll, the python binding only works with 32 bit python. Using it with 64 bit python will report "WindowsError:
[Error 193] %1 is not a valid Win32 application.".

Of course, it is only used for windows. And, if you already have thunder client installed, the download speed will be even faster.

