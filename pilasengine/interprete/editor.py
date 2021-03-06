# -*- encoding: utf-8 -*-
# pilas engine: un motor para hacer videojuegos
#
# Copyright 2010-2014 - Hugo Ruscitti
# License: LGPLv3 (see http://www.gnu.org/licenses/lgpl.html)
#
# Website - http://www.pilas-engine.com.ar
import codecs
import re
import sys
import os

from PyQt4.QtCore import Qt, QTimer
from PyQt4.Qt import (QFrame, QWidget, QPainter,
                      QSize, QVariant)
from PyQt4.QtGui import (QTextEdit, QTextCursor, QFileDialog,
                         QIcon, QMessageBox, QShortcut,
                         QKeySequence, QTextFormat, QColor, QKeyEvent)
from PyQt4.QtCore import Qt
from PyQt4 import QtCore

from editorbase import editor_base
import editor_ui
import pilasengine

CONTENIDO = u"""import pilasengine

pilas = pilasengine.iniciar()

mono = pilas.actores.Mono()

# Algunas transformaciones:
# (Pulsá el botón derecho del
#  mouse sobre alguna de las
#  sentencias)

mono.x = 0
mono.y = 0
mono.escala = 1.0
mono.rotacion = 0

pilas.ejecutar()"""


class WidgetEditor(QWidget, editor_ui.Ui_Editor):

    class NumberBar(QWidget):

        def __init__(self, *args):
            QWidget.__init__(self, *args)
            self.edit = None
            # This is used to update the width of the control.
            # It is the highest line that is currently visible.
            self.highest_line = 0

        def setTextEdit(self, edit):
            self.edit = edit

        def update(self, *args):
            width = self.fontMetrics().width(str(self.highest_line)) + 4

            if self.width() != width:
                self.setFixedWidth(width + 15)

            QWidget.update(self, *args)

        def paintEvent(self, event):
            contents_y = self.edit.verticalScrollBar().value()
            page_bottom = contents_y + self.edit.viewport().height()
            font_metrics = self.fontMetrics()

            painter = QPainter(self)

            line_count = 0

            block = self.edit.document().begin()

            while block.isValid():
                line_count += 1

                # The top left position of the block in the document
                position = self.edit.document().documentLayout().blockBoundingRect(block).topLeft()

                # Check if the position of the block is out side of the visible
                # area.
                if position.y() > page_bottom:
                    break

                # Draw the line number right justified at the y position of the
                # line. 3 is a magic padding number. drawText(x, y, text).
                painter.drawText(-5 + self.width() - font_metrics.width(str(line_count)) - 3,
                                round(position.y()) - contents_y + font_metrics.ascent(),
                                str(line_count))

                block = block.next()

            self.highest_line = line_count
            painter.end()

            QWidget.paintEvent(self, event)

    def __init__(self, main=None, interpreter_locals=None, consola_lanas=None, ventana_interprete=None, *args):
        QWidget.__init__(self, *args)
        self.setupUi(self)
        self.setLayout(self.vertical_layout)
        self.ruta_del_archivo_actual = None
        self.consola_lanas = consola_lanas
        self.ventana_interprete = ventana_interprete

        if interpreter_locals is None:
            interpreter_locals = locals()

        self.interpreter_locals = interpreter_locals
        self.lista_actores_como_strings = []

        self.editor = Editor(self, interpreter_locals, consola_lanas, ventana_interprete)
        self.editor.setFrameStyle(QFrame.NoFrame)
        self.editor.setAcceptRichText(False)

        self.number_bar = self.NumberBar()
        self.number_bar.setTextEdit(self.editor)

        # Agregando editor y number_bar a hbox_editor layout
        self.hbox_editor.addWidget(self.number_bar)
        self.hbox_editor.addWidget(self.editor)

        # Boton Abrir
        self.set_icon(self.boton_abrir, 'iconos/abrir.png')
        self.boton_abrir.connect(self.boton_abrir,
                                    QtCore.SIGNAL('clicked()'),
                                    self.editor.abrir_archivo_con_dialogo)

        # Boton Guardar
        self.set_icon(self.boton_guardar, 'iconos/guardar.png')
        self.boton_guardar.connect(self.boton_guardar,
                                    QtCore.SIGNAL('clicked()'),
                                    self.editor.guardar_contenido_con_dialogo)

        # Boton Ejecutar
        self.set_icon(self.boton_ejecutar, 'iconos/ejecutar.png')
        self.boton_ejecutar.connect(self.boton_ejecutar,
                                    QtCore.SIGNAL('clicked()'),
                                    self.cuando_pulsa_el_boton_ejecutar)

        # Boton Pausar
        self.set_icon(self.boton_pausar, 'iconos/pausa.png')
        self.boton_pausar.connect(self.boton_pausar,
                                    QtCore.SIGNAL('clicked()'),
                                    self.cuando_pulsa_el_boton_pausar)

        # Boton Siguiente
        self.set_icon(self.boton_siguiente, 'iconos/siguiente.png')
        self.boton_siguiente.connect(self.boton_siguiente,
                                    QtCore.SIGNAL('clicked()'),
                                    self.cuando_pulsa_el_boton_siguiente)

        self._vincular_atajos_de_teclado()

        self.editor.installEventFilter(self)
        self.editor.viewport().installEventFilter(self)

        self.timer_id = self.startTimer(1000 / 2.0)
        self.lista_actores.currentItemChanged.connect(self.cuando_selecciona_item)

    def definir_fuente(self, fuente):
        self.lista_actores.setFont(fuente)
        self.number_bar.setFont(fuente)

    def cuando_selecciona_item(self, actual, anterior):
        indice = self.lista_actores.indexFromItem(actual).row()
        if indice > -1:
            self.editor.cuando_selecciona_actor_por_indice(indice)

    def timerEvent(self, event):
        lista_actores = self.interpreter_locals['pilas'].escena._actores.obtener_actores()
        nueva_lista_de_actores = [str(x) for x in lista_actores]

        if self.lista_actores_como_strings != nueva_lista_de_actores:

            self.lista_actores.clear()
            #while self.lista_actores.count() > 0:
            #    self.lista_actores.takeItem(0)

            self.lista_actores_como_strings = nueva_lista_de_actores
            self.lista_actores.addItems(self.lista_actores_como_strings)

    def eventFilter(self, obj, event):
        if obj in (self.editor, self.editor.viewport()):
            self.number_bar.update()
            return False
        return QWidget.eventFilter(obj, event)

    def set_icon(self, boton, ruta):
        icon = QIcon()
        archivo = pilasengine.utils.obtener_ruta_al_recurso(ruta)
        icon.addFile(archivo, QSize(), QIcon.Normal, QIcon.Off)
        boton.setIcon(icon)
        boton.setText('')

    def _vincular_atajos_de_teclado(self):
        QShortcut(QKeySequence("F5"), self,
                  self.cuando_pulsa_el_boton_ejecutar)
        QShortcut(QKeySequence("Ctrl+r"), self,
                  self.cuando_pulsa_el_boton_ejecutar)

        # Solo en MacOS informa que la tecla Command sustituye a CTRL.
        if sys.platform == 'darwin':
            self.boton_ejecutar.setToolTip(u"Ejecutar el código actual (F5 o ⌘R)")

    def closeEvent(self, event):
        if not self.editor.salir():
            event.ignore()
            return

        event.accept()

    def cuando_pulsa_el_boton_ejecutar(self):
        self.editor.ejecutar(self.ruta_del_archivo_actual)
        self.boton_pausar.setChecked(False)

    def cuando_pulsa_el_boton_pausar(self):
        if self.boton_pausar.isChecked():
            self.editor.interpreterLocals['pilas'].widget.pausar()
        else:
            self.editor.interpreterLocals['pilas'].widget.continuar()

    def cuando_pulsa_el_boton_siguiente(self):
        if not self.boton_pausar.isChecked():
            self.boton_pausar.click()

        self.editor.interpreterLocals['pilas'].widget.avanzar_un_solo_cuadro()


class Editor(editor_base.EditorBase):
    """Representa el editor de texto que aparece en el panel derecho.

    El editor soporta autocompletado de código y resaltado de sintáxis.
    """

    # Señal es emitida cuando el Editor ejecuta codigo
    signal_ejecutando = QtCore.pyqtSignal()

    def __init__(self, main, interpreterLocals, consola_lanas, ventana_interprete):
        super(Editor, self).__init__()
        self.consola_lanas = consola_lanas
        self.ventana_interprete = ventana_interprete
        self.interpreterLocals = interpreterLocals
        self.insertPlainText(CONTENIDO)
        self.setLineWrapMode(QTextEdit.NoWrap)
        self._cambios_sin_guardar = False
        self.main = main

    def keyPressEvent(self, event):
        "Atiene el evento de pulsación de tecla."
        self._cambios_sin_guardar = True

        # Permite usar tab como seleccionador de la palabra actual
        # en el popup de autocompletado.
        if event.key() in [Qt.Key_Tab]:
            if self.completer and self.completer.popup().isVisible():
                event.ignore()
                nuevo_evento = QKeyEvent(QKeyEvent.KeyPress, Qt.Key_Return, Qt.NoModifier)
                try:
                    if self.autocomplete(nuevo_evento):
                        return None
                except UnicodeEncodeError:
                    pass
                return None


        if editor_base.EditorBase.keyPressEvent(self, event):
            return None


        # Elimina los pares de caracteres especiales si los encuentra
        if event.key() == Qt.Key_Backspace:
            self._eliminar_pares_de_caracteres()
            self._borrar_un_grupo_de_espacios(event)

        if self.autocomplete(event):
            return None


        if event.key() == Qt.Key_Return:
            cursor = self.textCursor()
            block = self.document().findBlockByNumber(cursor.blockNumber())
            whitespace = re.match(r"(\s*)", unicode(block.text())).group(1)

            linea_anterior = str(block.text()[:])
            cantidad_espacios = linea_anterior.count(' ') / 4

            if linea_anterior[-1:] == ':':
                whitespace = '    ' * (cantidad_espacios + 1)
            else:
                whitespace = '    ' * (cantidad_espacios)

            QTextEdit.keyPressEvent(self, event)
            return self.insertPlainText(whitespace)



        return QTextEdit.keyPressEvent(self, event)

    def _borrar_un_grupo_de_espacios(self, event):
        cursor = self.textCursor()
        block = self.document().findBlockByNumber(cursor.blockNumber())
        whitespace = re.match(r"(.*)", unicode(block.text())).group(1)

        if whitespace.endswith('    '):
            QTextEdit.keyPressEvent(self, event)
            QTextEdit.keyPressEvent(self, event)
            QTextEdit.keyPressEvent(self, event)

    def tiene_cambios_sin_guardar(self):
        return self._cambios_sin_guardar

    def _get_current_line(self):
        "Obtiene la linea en donde se encuentra el cursor."
        tc = self.textCursor()
        tc.select(QTextCursor.LineUnderCursor)
        return tc.selectedText()

    def _get_position_in_block(self):
        tc = self.textCursor()
        position = tc.positionInBlock() - 1
        return position

    def cargar_contenido_desde_archivo(self, ruta):
        "Carga todo el contenido del archivo indicado por ruta."
        with codecs.open(unicode(ruta), 'r', 'utf-8') as archivo:
            contenido = archivo.read()
        self.setText(contenido)

        self.nombre_de_archivo_sugerido = ruta
        self._cambios_sin_guardar = False

    def abrir_dialogo_cargar_archivo(self):
        return QFileDialog.getOpenFileName(self, "Abrir Archivo",
                                   self.nombre_de_archivo_sugerido,
                                   "Archivos python (*.py)",
                                   options=QFileDialog.DontUseNativeDialog)

    def abrir_archivo_con_dialogo(self):
        if self.tiene_cambios_sin_guardar():
            if self.mensaje_guardar_cambios_abrir():
                self.guardar_contenido_con_dialogo()

        ruta = self.abrir_dialogo_cargar_archivo()

        if ruta:
            ruta = str(ruta)
            self.cargar_contenido_desde_archivo(ruta)
            self.ruta_del_archivo_actual = ruta
            self.ejecutar(ruta)

    def mensaje_guardar_cambios_abrir(self):
        """Realizar una consulta usando un cuadro de dialogo simple
        se utiliza cuando hay cambios sin guardar y se desea abrir un archivo.
        Retorna True si el usuario presiona el boton *Guardar*,
        Retorna False si el usuario presiona *No*."""
        titulo = u"¿Deseas guardar el contenido antes de abrir un archivo?"
        mensaje = u"El contenido se perdera sino los guardas"

        mensaje = QMessageBox.question(self, titulo, mensaje, "Guardar", "No")

        return (not mensaje)

    def mensaje_guardar_cambios_salir(self):
        """Realizar una consulta usando un cuadro de dialogo simple
        se utiliza cuando hay cambios sin guardar y se desa salir del Editor.
        Retorna 0 si el usuario presiona el boton *Salir sin guardar*,
        Retorna 1 si el usuario presiona *Guardar*
        Retorna 2 si presiona *Cancelar*."""

        titulo = u"¿Deseas guardar el contenido antes de salir?"
        mensaje = u"El contenido se perdera sino los guardas"

        return QMessageBox.question(self, titulo, mensaje,
                                    "Salir sin guardar", "Guardar", "Cancelar")

    def marcar_error_en_la_linea(self, numero, descripcion):
        hi_selection = QTextEdit.ExtraSelection()

        hi_selection.format.setBackground(QColor(255, 220, 220))
        hi_selection.format.setProperty(QTextFormat.FullWidthSelection, QVariant(True))
        hi_selection.cursor = self.textCursor()
        posicion_linea = self.document().findBlockByLineNumber(numero).position()
        hi_selection.cursor.setPosition(posicion_linea)
        hi_selection.cursor.clearSelection()

        self.setExtraSelections([hi_selection])

    def guardar_contenido_con_dialogo(self):
        ruta = self.abrir_dialogo_guardar_archivo()

        if ruta:
            self.guardar_contenido_en_el_archivo(ruta)
            self._cambios_sin_guardar = False
            self.nombre_de_archivo_sugerido = ruta
            #self.mensaje_contenido_guardado()

    def salir(self):
        """Retorna True si puede salir y False si no"""
        if self.tiene_cambios_sin_guardar():
            mensaje = self.mensaje_guardar_cambios_salir()
            if mensaje == 1:
                self.guardar_contenido_con_dialogo()
            elif mensaje == 2:
                return False

        return True

    def obtener_contenido(self):
        return unicode(self.document().toPlainText())

    def ejecutar(self, ruta_personalizada=None):
        #print "ejecutando texto desde widget editor"
        texto = self.obtener_contenido()
        #texto = self.editor.obtener_texto_sanitizado(self)
        # elimina cabecera de encoding.
        contenido = re.sub('coding\s*:\s*', '', texto)
        contenido = contenido.replace('import pilasengine', '')
        contenido = contenido.replace('pilas = pilasengine.iniciar', 'pilas.reiniciar')

        for x in contenido.split('\n'):
            if "__file__" in x:
                contenido = contenido.replace(x, "# livecoding: " + x + "\n")

        # Muchos códigos personalizados necesitan cargar imágenes o sonidos
        # desde el directorio que contiene al archivo. Para hacer esto posible,
        # se llama a la función "pilas.utils.agregar_ruta_personalizada" con el
        # path al directorio que representa el script. Así la función "obtener_ruta_al_recurso"
        # puede evaluar al directorio del script en busca de recursos también.
        if ruta_personalizada:
            ruta_personalizada = ruta_personalizada.replace('\\', '/')
            ruta_personalizada = os.path.dirname(ruta_personalizada)
            agregar_ruta_personalizada = 'pilas.utils.agregar_ruta_personalizada("%s")' %(ruta_personalizada)
            contenido = contenido.replace('pilas.reiniciar(', agregar_ruta_personalizada+'\n'+'pilas.reiniciar(')

        try:
            exec(contenido, self.interpreterLocals)
        except Exception, e:
            self.consola_lanas.insertar_error_desde_exception(e)
            self.ventana_interprete.mostrar_el_interprete()
            #self.marcar_error_en_la_linea(10, "pepepe")

        self.signal_ejecutando.emit()

    def cuando_selecciona_actor_por_indice(self, indice):
        capturar_actor = "actor = pilas.obtener_actor_por_indice(" + str(indice) + ")"
        resaltar = "actor.transparencia = [50, 0] * 3, 0.1"
        exec(capturar_actor, self.interpreterLocals)
        exec(resaltar, self.interpreterLocals)
        self.consola_lanas.insertar_mensaje("# Creando la referencia 'actor': ")

if __name__ == '__main__':
    from PyQt4.QtGui import QApplication
    app = QApplication(sys.argv)
    weditor = WidgetEditor()
    weditor.show()
    app.exec_()
