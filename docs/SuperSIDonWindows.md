# SuperSID on Windows

If you want to use this version, you need to install the necessary envrionment first.

## Example of installation for Python 3.4.3

1. Download these 3 files:
  1.  python-3.4.3.msi from the official [Python site](http://python.org)
  2.  numpy-1.9.2+mkl-cp34-none-win32.whl from http://www.lfd.uci.edu/~gohlke/pythonlibs/#numpy
  3.  PyAudio-0.2.8-cp34-none-win32.whl from http://www.lfd.uci.edu/~gohlke/pythonlibs/#pyaudio
2.  Execute *python-3.4.3.msi* to install *Python 3.4*
3.  Install *numpy* with `C:\Python34\Scripts\pip.exe install numpy-1.9.2+mkl-cp34-none-win32.whl`
3.  Install *matplotlib* and its dependencies with `C:\Python34\Scripts\pip.exe install matplotlib`
4.  Install *PyAudio* with `C:\Python34\Scripts\pip.exe install PyAudio-0.2.8-cp34-none-win32.whl`

As you can notice, **wxPython** is absent as not ported on Python 3. Instead use the TkInter GUI by indicating `viewer=tk` in your .cfg file (cf below paragraph).

## SuperSID installtion

Once the environment is setup, fetch the application:
 - You can simply go to https://github.com/ericgibert/supersid and click on the "Download ZIP" button
**OR**
 - You can first install Git on Windows: http://msysgit.github.io/
	- I have installed: Git-1.8.3-preview20130601.exe
 - Then issue the command: ````git clone https://github.com/ericgibert/supersid.git````
 - In the future, move to *supersid* directory and issue the command ````git pull```` to download the latest updates


## Adapting your .cfg file

For Graphic User Interface, use supersid\Config\supersid.tk.cfg :
````
	[PARAMETERS]
	viewer=tk
	site_name = CHEZMOI
	data_path = C:\Documents and Settings\eric\My Documents\supersid\Data
````
then call ````supersid\supersid.py Config\supersid.tk.cfg````


Similare changes can be performed to the Config\supersid.text.cfg file for text mode:
 - Text mode declaration 
 - Change the data_path to a Windows target directory
 - Choose a name for your site

````
	[PARAMETERS]
	viewer=text
	site_name = CHEZMOI
	data_path = C:\Documents and Settings\eric\My Documents\supersid\Data
````

then call ````supersid\supersid.py Config\supersid.text.cfg````
