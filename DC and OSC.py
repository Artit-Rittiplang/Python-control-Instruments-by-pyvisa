import pyvisa
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import tkinter
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from PIL import Image, ImageTk
import numpy as np

########## Oscilloscope ##############
Keysight_scope = pyvisa.ResourceManager()
scope = Keysight_scope.open_resource('USB0::0x2A8D::0x039B::CN63261167::INSTR')
scope.write(":DIGitize CHANnel1")
scope.write(":WAVeform:SOURce CHANnel1")
scope.write(":WAVeform:FORMat BYTE")

def Scale_Ch1():
    global scale1
    scope.write(":CHANnel1:SCALe " + scale1.get())

def Horizontal():
    global Time_scale
    scope.write(":TIMebase:SCALe " + Time_scale.get())

################################## DC supply ############
Keysight_DC = pyvisa.ResourceManager()
DC = Keysight_DC.open_resource('USB0::0x2A8D::0x8F01::CN63150019::INSTR')
DC.write("INSTrument:NSELect 1")

class CH1():
    def __init__(self, val1):
        self.volt = val1

    def volt_ch1(self):
        DC.write("INSTrument:NSELect 1")
        DC.write("VOLT " + self.volt.get() + ",(@1)")

    def on_ch1(self):
        DC.write("OUTPut:STAT on")

    def off_ch1(self):
        DC.write("OUTPut:STAT off")

###################################
############# Create GUI ##########
###################################
root = tkinter.Tk()
ubo_frame = tkinter.Frame(root)

# UBU Image
UBU = Image.open(r'G:\My Drive\(HOT) UBU\งานโชว์\Python for instruments\ubu.png')
UBU = UBU.resize((400, 150))
UBU_img = ImageTk.PhotoImage(UBU)
tkinter.Label(ubo_frame, image=UBU_img).pack()
ubo_frame.pack(side=tkinter.TOP, pady=10)

# Figure and Axes (Time + FFT)
fig, (ax, ax_fft) = plt.subplots(2, 1, figsize=(6, 6))
fig.tight_layout(pad=4)

# Title label
average_voltage_label = tkinter.Label(root, text="Mechatronics Engineering", font=("Arial", 24, "bold"), bg="#f0f0f0", fg="#333333", padx=10, pady=5)
average_voltage_label.pack(side=tkinter.TOP, pady=5)

def animate(i):
    try:
        y = scope.query_binary_values(":WAVeform:DATA?", datatype='s', is_big_endian=True)
        dy = float(scope.query(":WAVeform:YINCrement?"))
        yoff = float(scope.query(":WMEMory1:YOFFset?"))
        yref = float(scope.query(":WAVeform:YREFerence?"))
        y = np.array(y, dtype=np.float64)
        y = (y - yref) * dy - yoff

        time_per_div = float(scope.query(":TIMebase:SCALe?"))
        max_time = time_per_div * 10
        dt = max_time / len(y)
        x = np.arange(0, len(y)) * dt

        # Clear axes
        ax.clear()
        ax_fft.clear()

        # Time Domain Plot
        ax.plot(x, y)
        ax.set_xlabel("Time (s)")
        ax.set_ylabel("Voltage (V)")
        ax.set_title("Time-Domain Waveform")
        ax.set_xlim(x[0], x[-1])
        ax.set_ylim(-1, 7)

        # FFT
        yf = np.fft.fft(y)
        xf = np.fft.fftfreq(len(y), dt)
        idx = np.argsort(xf)
        xf = xf[idx]
        yf = np.abs(yf)[idx]

        # Only positive frequencies
        mask = xf > 0
        xf = xf[mask]
        yf = yf[mask]

        ax_fft.plot(xf, yf)
        ax_fft.set_xlabel("Frequency (Hz)")
        ax_fft.set_ylabel("Amplitude")
        ax_fft.set_title("FFT Spectrum")
        ax_fft.set_xlim(0, np.max(xf) * 0.5)

    except Exception as e:
        print("Error in animate:", e)

ani = animation.FuncAnimation(fig, animate, frames=100, interval=25, repeat=True)
canvas = FigureCanvasTkAgg(fig, master=root)
canvas.get_tk_widget().pack(side='top', fill='both', expand=True)

############ ON/OFF Button ############
pause = True
def pause_animation():
    global pause
    if pause:
        ani.event_source.stop()
        pause = False
    else:
        ani.event_source.start()
        pause = True

# Layout: Oscilloscope + DC Supply
main_frame = tkinter.Frame(root)
main_frame.pack(side='top', fill='both', expand=True)

# Oscilloscope ON/OFF Frame
fm_ONOFF = tkinter.Frame(main_frame)
tkinter.Label(fm_ONOFF, text='Oscilloscope', font=("Arial Bold", 18)).pack(side=tkinter.LEFT)
button_run = tkinter.Button(fm_ONOFF, text="ON/OFF", command=pause_animation, font=('Arial Bold', 14), bg="yellow", fg="black")
button_run.pack(side=tkinter.LEFT)

button_quit = tkinter.Button(fm_ONOFF, text="Quit", command=root.quit, font=('Arial Bold', 14), bg="red", fg="black")
button_quit.pack(side=tkinter.LEFT)
fm_ONOFF.pack(side=tkinter.LEFT, padx=10, pady=10)

# Oscilloscope control
fm_OS = tkinter.Frame(main_frame)
Label_ScaleCh1 = tkinter.Label(fm_OS, text='Scale Ch1', font=("Arial Bold", 14))
Label_ScaleCh1.pack(side=tkinter.LEFT, padx=5)
scale1 = tkinter.Entry(fm_OS, font=("Arial Bold", 14))
scale1.pack(side=tkinter.LEFT, padx=5)
ok_scale1 = tkinter.Button(fm_OS, text='OK', command=Scale_Ch1, font=("Arial Bold", 14))
ok_scale1.pack(side=tkinter.LEFT, padx=5)

Label_TimeScale = tkinter.Label(fm_OS, text='Time Scale', font=("Arial Bold", 14))
Label_TimeScale.pack(side=tkinter.LEFT, padx=5)
Time_scale = tkinter.Entry(fm_OS, font=("Arial Bold", 14))
Time_scale.pack(side=tkinter.LEFT, padx=5)
ok_Time_Scale = tkinter.Button(fm_OS, text='OK', command=Horizontal, font=("Arial Bold", 14))
ok_Time_Scale.pack(side=tkinter.LEFT, padx=5)
fm_OS.pack(side=tkinter.LEFT, padx=10, pady=10)

# DC Power Supply controls
fm_ch1 = tkinter.Frame(main_frame)
Ch1_Label = tkinter.Label(fm_ch1, text='Volt Ch1', font=("Arial Bold", 14))
Ch1_Label.pack(side=tkinter.LEFT)
val1 = tkinter.Entry(fm_ch1, font=("Arial Bold", 14))
val1.pack(side=tkinter.LEFT)

ch1_instance = CH1(val1)

Ch1_Ok = tkinter.Button(fm_ch1, text='OK', command=ch1_instance.volt_ch1, font=("Arial Bold", 14))
Ch1_Ok.pack(side=tkinter.LEFT)
On_CH1 = tkinter.Button(fm_ch1, text="On Ch1", command=ch1_instance.on_ch1, font=("Arial Bold", 14), bg="green", fg="black")
On_CH1.pack(side=tkinter.LEFT)
Off_CH1 = tkinter.Button(fm_ch1, text="Off Ch1", command=ch1_instance.off_ch1, font=("Arial Bold", 14), bg="red", fg="black")
Off_CH1.pack(side=tkinter.LEFT)

fm_ch1.pack(side=tkinter.RIGHT, padx=10, pady=10)

# Proper shutdown
def on_closing():
    scope.close()
    DC.close()
    root.quit()

root.protocol("WM_DELETE_WINDOW", on_closing)
tkinter.mainloop()
