# -*- coding: utf-8 -*-
# pilas engine: un motor para hacer videojuegos
#
# Copyright 2010-2014 - Hugo Ruscitti
# License: LGPLv3 (see http://www.gnu.org/licenses/lgpl.html)
#
# Website - http://www.pilas-engine.com.ar
import codecs
import os
import sys
import time

from PyQt4 import QtCore
from PyQt4.QtGui import (QKeySequence, QIcon, QLabel, QMainWindow)

import lanas
from pilasengine import utils
import pilasengine
from pilasengine.interprete import editor

from ventana_interprete import VentanaInterprete


def abrir():
    MainWindow = QMainWindow()

    ui = VentanaInterprete()
    ui.setupUi(MainWindow)

    utils.centrar_ventana(MainWindow)
    MainWindow.show()
    MainWindow.raise_()

    return MainWindow


def abrir_script_con_livereload(archivo):
    MainWindow = QMainWindow()

    ui = VentanaInterprete()
    ui.setupUi(MainWindow)

    utils.centrar_ventana(MainWindow)
    MainWindow.show()
    ui.colapsar_interprete()
    MainWindow.raise_()
    ui.editor.cargar_contenido_desde_archivo(archivo)
    ui.editor.ejecutar(archivo)


    return MainWindow
