# What PyInstaller Does and How It Does It
##Section: Analysis: Finding the Files Your Program Needs
Some Python scripts import modules in ways that PyInstaller cannot detect,
you can help PyInstaller:
> - You can give additional files on the pyinstaller command line.
> - You can give additional import paths on the command line.
> - You can edit the myscript.spec file that PyInstaller writes the first time you run it 
>for your script. In the spec file you can tell PyInstaller about code modules 
>that are unique to your script.  

---
## Section: Bundling to One Folder
...
## Section: How the one-folder program works