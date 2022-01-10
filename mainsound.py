from PyQt5 import QtWidgets, uic
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QPushButton, QVBoxLayout, QFileDialog, QGraphicsView
import sys
from PyQt5.uic.properties import QtCore
from PyQt5.QtCore import pyqtSignal
import numpy as np
from pylab import plot, show, axis
from pyqtgraph import PlotWidget, plot
import pandas as pd
from scipy import signal
import os
import scipy.io.wavfile
# import librosa.display
import img_rc
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent, QMediaPlaylist
from PyQt5.QtCore import Qt, QUrl
import logging
import pyqtgraph as pg

import matplotlib
from datetime import datetime
from mpl_toolkits.axes_grid1.axes_divider import make_axes_locatable

matplotlib.use('Qt5Agg')
from PyQt5 import QtCore
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import (NavigationToolbar2QT as NavigationToolbar)
import logging
import math
import wave
import random

from music21 import *

logger = logging.getLogger()
logger.setLevel(logging.INFO)
logging.basicConfig(format='%(asctime)s %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s',
                    datefmt='%d-%m-%Y:%H:%M:%S',
                    level=logging.DEBUG,
                    filename='Audio.txt')


def hhmmss(ms):
    # s = 1000
    # m = 60000
    # h = 360000
    h, r = divmod(ms, 36000)
    m, r = divmod(r, 60000)
    s, _ = divmod(r, 1000)
    return ("%d:%02d:%02d" % (h, m, s)) if h else ("%d:%02d" % (m, s))


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        uic.loadUi('soundgui.ui', self)

        self.player1 = QMediaPlayer()
        self.player2 = QMediaPlayer()

        self.actionOpen.triggered.connect(self.open)
        self.mediaPlayer = QMediaPlayer(None, QMediaPlayer.VideoSurface)

        self.play_btn_before_2.clicked.connect(self.player1.play)
        self.play_btn_before_2.clicked.connect(self.plot_graph)
        self.play_btn_before_2.clicked.connect(self.plot_spectogram)
        self.pause_btn_before_2.clicked.connect(self.player1.pause)
        self.stop_btn_before_2.clicked.connect(self.player1.stop)
        self.volumeSlider1.valueChanged.connect(self.player1.setVolume)

        self.play_btn_after_2.clicked.connect(self.player2.play)
        self.play_btn_after_2.clicked.connect(self.plot_graph2)
        self.play_btn_after_2.clicked.connect(self.plot_spectogram2)

        self.pause_btn_after_2.clicked.connect(self.player2.pause)
        self.stop_btn_after_2.clicked.connect(self.player2.stop)
        self.volumeSlider2.valueChanged.connect(self.player2.setVolume)

        self.player1.durationChanged.connect(self.update_duration)
        self.player1.positionChanged.connect(self.update_position)
        self.timeSlider1.valueChanged.connect(self.player1.setPosition)
        self.setAcceptDrops(True)

        self.MplWidget.canvas.axes.set_facecolor('black')
        self.MplWidget2.canvas.axes.set_facecolor('black')
        self.show()

        self.bands_powers = [0.0, 0.25, 0.50, 0.75, 1.0, 2.0, 3.0, 4.0, 5.0]
        self.modified_signal = np.array([])
        self.current_slider_gain = [1.0] * 10

        self.band_slider = {}

        for index in range(10):
            self.band_slider[index] = getattr(self, 'band_{}'.format(index + 1))

        for index, slider in self.band_slider.items():
            slider.sliderReleased.connect(lambda index=index: self.slider_gain_updated(index))

        self.show()

    # ===============================================Instruments=========================#
    def keyPressEvent(self, event):
        # To Get ASCII Value
        pressed = chr(event.key())

        XylophoneDict = {"1": "A", "2": "B", "3": "C", "4": "D", "5": "E", "6": "F", "7": "G", "8": "A#", "9": "B#"}
        PianoDict = {"Q": "A", "W": "B", "E": "C", "R": "D", "T": "E", "Y": "F", "U": "G", "I": "A#", "O": "B#"}

        if pressed in PianoDict:
            # print(PianoDict[pressed])
            notes = PianoDict[pressed]
            x = instrument.Piano()
            keyNote = note.Note(notes)
            keyNote.duration.quarterLength = 1
            keyNote.volume.velocity = 127
            output_notes = []
            output_notes.append(x)
            output_notes.append(keyNote)
            streamNote = stream.Stream(output_notes)
            midi.realtime.StreamPlayer(streamNote).play(playForMilliseconds=50, blocked=False)

        if pressed in XylophoneDict:
            notes = XylophoneDict[pressed]
            x = instrument.Xylophone()
            keyNote = note.Note(notes)
            keyNote.duration.quarterLength = 1
            keyNote.volume.velocity = 127
            output_notes = []
            output_notes.append(x)
            output_notes.append(keyNote)
            streamNote = stream.Stream(output_notes)
            midi.realtime.StreamPlayer(streamNote).play(playForMilliseconds=50, blocked=False)

            # ===============================================Bongo===============================================#

        def Bongo():
            x = instrument.BongoDrums()
            keyNote = chord.Chord([self.horizontalSlider.value()])
            keyNote.duration.quarterLength = 1
            keyNote.volume.velocity = 127
            output_notes = []
            output_notes.append(x)
            output_notes.append(keyNote)
            streamNote = stream.Stream(output_notes)
            midi.realtime.StreamPlayer(streamNote).play(playForMilliseconds=50, blocked=False)

        if event.key() == QtCore.Qt.Key_B:
            logging.info('User is playing Bongo and pressed B')
            # notes = 'A2'
            Bongo()
        if event.key() == QtCore.Qt.Key_N:
            logging.info('User is playing Bongo and pressed N')
            # notes = 'E2'
            Bongo()

    def open(self):
        global data
        try:
            path = QFileDialog.getOpenFileName(self, 'Open a file', '', 'Audio File(*.wav)')
        except wave.Error:
            logging.error("The user didn't open a .wav file")

        if path != ('', ''):
            data = path[0]
            self.player1.setMedia(QMediaContent(QUrl.fromLocalFile(data)))
            self.sampling_rate, self.samples = scipy.io.wavfile.read(data)
            logging.info("The user open an audio file path: " + data)

    def plot_graph(self):
        global sampling_rate
        global samples
        sampling_rate, samples = scipy.io.wavfile.read(data)
        self.graph_before_2.clear()
        peak_value = np.amax(samples)
        normalized_data = samples / peak_value
        length = samples.shape[0] / sampling_rate
        time = list(np.linspace(0, length, samples.shape[0]))
        drawing_pen = pg.mkPen(color=(255, 0, 0), width=0.5)
        self.graph_before_2.plotItem.setLabel(axis='left', text='Amplitude')
        self.graph_before_2.plotItem.setLabel(axis='bottom', text='time [s]')
        # self.graph_before_2.plotItem.getViewBox().setLimits(xMin=0, xMax=np.max(time), yMin=-1.1, yMax=1.1)
        self.graph_before_2.setXRange(0, 0.1)
        self.graph_before_2.plot(time, normalized_data, pen=drawing_pen)
        logging.info('User is ploting the original signal')

    def plot_graph2(self):
        global sampling_rate2
        global samples2
        sampling_rate2, samples2 = scipy.io.wavfile.read(f'{self.now}Output.wav')
        self.graph_after_2.clear()
        peak_value = np.amax(samples2)
        normalized_data2 = samples2 / peak_value
        length = samples2.shape[0] / sampling_rate2
        time2 = list(np.linspace(0, length, samples2.shape[0]))
        drawing_pen = pg.mkPen(color=(0, 0, 255), width=0.5)
        self.graph_after_2.plotItem.setLabel(axis='left', text='Amplitude')
        self.graph_after_2.plotItem.setLabel(axis='bottom', text='time [s]')
        self.graph_after_2.plotItem.getViewBox().setLimits(xMin=0, xMax=np.max(time2), yMin=-1.1, yMax=1.1)
        self.graph_after_2.plot(time2, normalized_data2, pen=drawing_pen)
        logging.info('User is ploting the equilized signal')

    def plot_spectogram(self):
        self.MplWidget.canvas.axes.clear()
        self.MplWidget.canvas.axes.tick_params(axis="x", colors="red")
        self.MplWidget.canvas.axes.tick_params(axis="y", colors="red")
        self.MplWidget.canvas.axes.specgram(samples, Fs=sampling_rate)
        self.MplWidget.canvas.draw()
        logging.info('User is ploting the original specgram')

    def plot_spectogram2(self):
        self.MplWidget2.canvas.axes.clear()
        self.MplWidget2.canvas.axes.tick_params(axis="x", colors="blue")
        self.MplWidget2.canvas.axes.tick_params(axis="y", colors="blue")
        self.MplWidget2.canvas.axes.specgram(samples2, Fs=sampling_rate2)
        self.MplWidget2.canvas.draw()
        logging.info('User is ploting the equilized specgram')

    def modify_signal(self):
        frequency_content = np.fft.rfftfreq(len(self.samples), d=1 / self.sampling_rate)
        modified_signal = np.fft.rfft(self.samples)
        for index, slider_gain in enumerate(self.current_slider_gain):
            frequency_range_min = (index + 0) * self.sampling_rate / (2 * 10)
            frequency_range_max = (index + 1) * self.sampling_rate / (2 * 10)
            range_min_frequency = frequency_content > frequency_range_min
            range_max_frequency = frequency_content <= frequency_range_max
            slider_min_max = []
            for is_in_min_frequency, is_in_max_frequency in zip(range_min_frequency, range_max_frequency):
                slider_min_max.append(is_in_min_frequency and is_in_max_frequency)
            modified_signal[slider_min_max] *= slider_gain
        self.samples_after = np.fft.irfft(modified_signal)
        self.now = datetime.now()
        self.now = f'{self.now:%Y-%m-%d %H-%M-%S.%f %p}'
        scipy.io.wavfile.write(f'{self.now}Output.wav', self.sampling_rate, self.samples_after.astype(np.int16))
        self.player2.setMedia(QMediaContent(QUrl.fromLocalFile(f'{self.now}Output.wav')))
        logging.info('User modified the EQ')

    def slider_gain_updated(self, index):
        slider_gain = self.bands_powers[self.band_slider[index].value()]
        # self.band_label[index].setText(f'{slider_gain}')
        self.current_slider_gain[index] = slider_gain
        self.modify_signal()

    def update_duration(self, duration):
        self.timeSlider1.setMaximum(duration)
        if duration >= 0:
            self.total_time_before_2.setText(hhmmss(duration))

    def update_position(self, position):
        if position > 0:
            self.current_time_before_2.setText(hhmmss(position))
            self.graph_before_2.setXRange((position / 1000) - 0.1, (position / 1000))

        # Disable the events to prevent updating triggering a setPosition event (can cause stuttering).
        self.timeSlider1.blockSignals(True)
        self.timeSlider1.setValue(position)
        self.timeSlider1.blockSignals(False)


app = 0
app = QtWidgets.QApplication(sys.argv)
window = MainWindow()
app.exec_()