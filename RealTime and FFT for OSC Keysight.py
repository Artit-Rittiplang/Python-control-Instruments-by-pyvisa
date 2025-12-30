
from quantiphy import Quantity
import pyvisa
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation


Keysight = pyvisa.ResourceManager()
scope= Keysight.open_resource('USB0::0x2A8D::0x039B::CN63261167::INSTR')
# scope.write('Comm_HeaDeR OFF')

# create a main figure
fig = plt.figure()
# prepare a graph (y-axis and x-axis) onto the main figure
ax1 = fig.add_subplot(2,1,1)
ax2 = fig.add_subplot(2,1,2)
def animate(i):
    data_unscaled = scope.query_binary_values(":WAVeform:DATA?",datatype='b')
    vdiv = scope.query()
    offset = scope.query(':CHANnel<n>:OFFSet?')
    t_resolution = 1/Quantity(scope.query('SARA?')).real
    N = len(data_unscaled)
    x = range(0,N)
    data_scaled = np.dot(data_unscaled,2*vdiv/25-offset)
    t = np.dot(x,t_resolution)
    # clear the old graph when we have new one to avoid out of memory
    ax1.clear()
    ax1.plot(t,data_scaled)
    ax1.set_xlabel("Time")
    ax1.set_ylabel("Amplitude")

    ### FFT
    Mag = abs(np.fft.fftshift(np.fft.fft(data_scaled)));
    Mag = 20 * np.log10(Mag / max(Mag));
    df = 1 / (max(t) - min(t));
    f = np.linspace(-N * df / 2, N * df / 2 - df, N)  # frequency domain
    ax2.clear()
    ax2.plot(f, Mag)
    ax2.set_xlabel("Frequency [Hz]")
    ax2.set_ylabel("Magnitude")
    ax2.set_xlim([-10000, 10000])
    ax2.set_ylim([-10, 1])

ani = FuncAnimation(fig,animate, interval=25)
###### interval represents the delay between each frame in milliseconds
###### interval default is 100
plt.show()
scope.close() # close scope

