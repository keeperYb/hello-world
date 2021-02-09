# 《PyInstaller打包实战指南》
## 第一篇 PyInstaller打包基础
### 第一节 安装PyInstaller
...
---
### 第二节 PyInstaller的两种打包模式
#### 1. 文件夹模式打包
> Tips:  
>同时按住shift键和鼠标右键，选择“在此处打开命令行窗口“(或者是"在此处打开Powershell窗口"), 可以打开
>powershell.

#### 2. 单文件模式打包
要打包成单个文件，我们只需要加一个-F命令：
```
pyinstaller -F belle.py
```

#### 3. build, dist和spec文件(夹)简介  
- **build 文件夹**  
存放生成的一些日志文件以及工作文件
- **dist 文件夹**  
存放已经打包好的文件
- **spec 文件**  
存储着打包时所用的命令以及要打包的相关文件，告诉PyInstaller如何处理

---
### 第三节 黑框的调试作用以及如何去掉黑框
#### 1. 在黑框中查看报错信息
使用tkinter编写一个简单的页面:
```python
import tkinter

win = tkinter.Tk()
win.iconbitmap('./icon.ico')    # 设置窗口图标
win.mainloop()
```
> Tips:
> 黑框消失得很快, 可以
> - 代码中加入os.system('pause')  
>   or
> - 将 *.exe 拖到 shell 中 

#### 2. 如何去掉黑框  
加上-w(小写)即可
```
pyinstaller -F -w belle.py
```
> Tips:  
> 建议平常保留黑框, 只在经过严格测试, 需要交付软件时, 才去掉黑框

---
### 第四节 给应用程序加上图标
加入 -i 来添加图标:
```
pyinstaller -F -w -i ./smile.ico belle.py
```
> Tips:  
> \*.ico 图标文件需要经过**格式转化**而来, 不能靠简单修改后缀

---
### 第五节 其他基础命令
> -h   
>该命令可以显示PyInstaller的帮助信息，使用后读者可以看到所有PyInstaller命令的用法和解释

> -v  
> Check the version of PyInstaller

> -n=NAME  
>  Name to assign to the bundled app and spec file

> -y   
>  Replace output directory (default:SPEC_PATH\dist\SPEC_NAME) without asking confirmation

> --distpath=DIR  
> Where to put the bundled app (default: .\dist)

> --clean   
> Clean PyInstaller cache and remove temporary before building.

> --hidden-import MODULENAME, --hiddenimport MODULENAME  
> Name an import not visible in the code of script(s). This option can be used **multiple times**.

### 第六节 使用批处理文件快速打包
1. 编写批处理文件
2. 生成依赖环境  

一种方法: 
```
pip freeze > requirements.txt
```
但是 freeze 将整个环境的依赖都加上了, 过于冗余.  
实际可以用一下命令来生成requirements.txt:  
```
pipreqs ./
```
在实际使用时, 输入:
```
pip install -r requirements.txt
```

## 第二篇 PyInstaller打包进阶
### 第七节 可执行文件运行时发生了什么
1. 文件夹模式下如何运行  
在双击exe运行后, 会调用启动装置(BootLoader)来准备运行环境
2. 单文件模式下如何运行  
在双击exe后, pyinstaller会进行解压, 复制, 将用户程序需要的依赖都置于__MEIxx的文件中, 此文件可以通过
在代码中加入如下一行来查看(只有打包运行后, 这一行才有效)
```
print(sys._MEIPASS)
```
正因为有了解压, 复制的操作, 单文件的用户程序在第一次运行时会比较慢  
在程序正常退出后, 临时文件夹会被删除

### 第八节 打包资源文件
需要注意 --add-data 和 --add-binary 两个参数选项
>  --add-data <SRC;DEST or SRC:DEST>  
> Additional non-binary files or folders to be added to the executable. The path separator is 
> platform specific, \`\`os.pathsep\`\` (which is ``;`` on Windows and ``:`` on 
> most unix systems) is used. This option can be used multiple times.  
>
>具体使用方法如下 (格外注意=后面的写法...):
>```
>pyinstaller.exe -F -w --add-data="icon.ico;." .\tkinter_gui.py
>```
#### 1. 添加图片
实际上, 用到了自身代码中的 res_path方法, 如下:
```python
import tkinter
import sys
import os


# What helps us to confirm the absolute path of resource
def res_path(relative_path):
    """get absolute path of resource file"""
    try:
        base_path = sys._MEIPASS  # sys._MEIPASS was introduced in last section...
    except:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

win = tkinter.Tk()
win.iconbitmap(res_path('./icon.ico'))    # call the func here, 设置窗口图标
win.mainloop()
```
#### 2. 添加可执行文件
和 1. 添加图片 相似
#### 3. 添加压缩文件
...
