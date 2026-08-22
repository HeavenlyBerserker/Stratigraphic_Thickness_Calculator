[app]

# title of your application
title = Stratigraphic_Thickness_Calculator_MacOS

# project root directory. default = The parent directory of input_file
# must be the repo root so ``from source...`` imports resolve during packaging.
project_dir = ..

# root entry point (not source/main.py) = keeps the ``source`` package intact.
input_file = /Users/hong/Projects/Stratigraphic_Thickness_Calculator/main.py

# directory where the executable output is generated
exec_directory = .

# path to the project file relative to project_dir
project_file = 

# application icon (png is converted to .icns during the macos build)
icon = ../logo.png

[python]

# python path (updated automatically when you run pyside6-deploy from an active env)
python_path = /opt/anaconda3/bin/python3.13

# python packages to install
packages = Nuitka==2.7.11

# buildozer = for deploying Android application
android_packages = buildozer==1.5.0,cython==0.29.33

[qt]

# paths to required qml files. comma separated
# normally all the qml files required by the project are added automatically
# design studio projects include the qml files using qt resources
qml_files = 

# excluded qml plugin binaries
excluded_qml_plugins = 

# qt modules used. comma separated
modules = Core,DBus,Gui,Widgets

# qt plugins used by the application. only relevant for desktop deployment
# for qt plugins used in android application see [android][plugins]
plugins = accessiblebridge,egldeviceintegrations,generic,iconengines,imageformats,platforminputcontexts,platforms,platforms/darwin,platformthemes,styles,wayland-decoration-client,wayland-graphics-integration-client,wayland-shell-integration,xcbglintegrations

[android]

# path to pyside wheel
wheel_pyside = 

# path to shiboken wheel
wheel_shiboken = 

# plugins to be copied to libs folder of the packaged application. comma separated
plugins = 

[nuitka]

# usage description for permissions requested by the app as found in the info.plist file
# of the app bundle. comma separated
# eg = extra_args = --show-modules --follow-stdlib
macos.permissions = 

# mode of using nuitka. accepts standalone or onefile. default = onefile
mode = onefile

# specify any extra nuitka arguments
# --macos-app-name sets cfbundlename / cfbundledisplayname (menu bar title)
# --include-package = source ensures the desktop package is compiled into the app
extra_args = --quiet --noinclude-qt-translations --include-package=source --macos-app-name="Stratigraphic Thickness Calculator" --macos-signed-app-name=org.stratigraphic.thickness.calculator

[buildozer]

# build mode
# possible values = ["aarch64", "armv7a", "i686", "x86_64"]
# release creates a .aab, while debug creates a .apk
mode = debug

# path to pyside6 and shiboken6 recipe dir
recipe_dir = 

# path to extra qt android .jar files to be loaded by the application
jars_dir = 

# if empty, uses default ndk path downloaded by buildozer
ndk_path = 

# if empty, uses default sdk path downloaded by buildozer
sdk_path = 

# other libraries to be loaded at app startup. comma separated.
local_libs = 

# architecture of deployed platform
arch = 

