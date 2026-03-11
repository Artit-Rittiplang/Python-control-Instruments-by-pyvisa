import pyvisa
import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import tkinter
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from PIL import Image, ImageTk
import numpy as np

###### Initialize Oscilloscope and DC Supply
Keysight_scope = pyvisa.ResourceManager()
scope = Keysight_scope.open_resource('USB0::0x2A8D::0x039B::CN63261167::INSTR')
scope.write(":DIGitize CHANnel1")
scope.write(":WAVeform:SOURce CHANnel1")
scope.write(":WAVeform:FORMat BYTE")
Keysight_DC = pyvisa.ResourceManager()
DC = Keysight_DC.open_resource('USB0::0x2A8D::0x8F01::CN63150115::INSTR')
DC.write("INSTrument:NSELect 1")

def Scale_Ch1():
    global scale1
    scope.write(":CHANnel1:SCALe " + scale1.get())

def Horizontal():
    global Time_scale
    scope.write(":TIMebase:SCALe " + Time_scale.get())

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
root.title("Oscilloscope Motor Analysis")
ubo_frame = tkinter.Frame(root)

# UBU Image
try:
    UBU = Image.open(r'G:\My Drive\งานวิจัยเครื่องมือวัด\enUBU.JPG')
    UBU = UBU.resize((600, 200))
    UBU_img = ImageTk.PhotoImage(UBU)
    tkinter.Label(ubo_frame, image=UBU_img).pack()
except FileNotFoundError:
    pass
ubo_frame.pack(side=tkinter.TOP, pady=10)

# Create 2 subplot figure: time-domain + FFT
fig, (ax, ax_fft) = plt.subplots(2, 1, figsize=(6, 6))
fig.tight_layout(pad=4.5)


def animate(i):
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

    ax.clear()
    ax_fft.clear()

    ax.plot(x, y)
    ax.set_xlabel("Time (s)", fontsize=14)
    ax.set_ylabel("Voltage (V)", fontsize=14)
    ax.set_title("Time-Domain Waveform", fontsize=16)
    ax.tick_params(axis='both', labelsize=12)
    ax.set_xlim(x[0], x[-1])
    #ax.set_ylim(-1, 5)

    yf = np.fft.fft(y)
    xf = np.fft.fftfreq(len(y), dt)
    idx = np.argsort(xf)
    xf = xf[idx]
    yf = np.abs(yf)[idx]

    mask = xf > 0
    xf = xf[mask]
    yf = yf[mask]

    threshold = 0.05 * np.max(yf)
    significant = np.where(yf > threshold)[0]
    
    if significant.size > 0:
        max_freq = xf[significant[-1]]
        ax_fft.set_xlim(0, max_freq * 1.1)
    else:
        ax_fft.set_xlim(0, np.max(xf))

    # Calculate RPM and add it to the FFT plot legend
    if len(yf) > 0:
        peak_idx = np.argmax(yf)
        peak_freq = xf[peak_idx]
        estimated_rpm = peak_freq * 60.0
        rpm_text = f"Speed: {estimated_rpm:.0f} RPM"
    else:
        rpm_text = "Speed: 0 RPM"

    ax_fft.plot(xf, yf, label=rpm_text)
    ax_fft.legend(loc='upper right', fontsize=20, labelcolor='black') 
    
    ax_fft.set_xlabel("Frequency (Hz)", fontsize=14)
    ax_fft.set_ylabel("Amplitude", fontsize=14)
    ax_fft.set_title("FFT Spectrum", fontsize=16)
    ax_fft.tick_params(axis='both', labelsize=12)

ani = animation.FuncAnimation(fig, animate, interval=100, cache_frame_data=False) 
canvas = FigureCanvasTkAgg(fig, master=root)
canvas.get_tk_widget().pack(side='top', fill='both', expand=True)

############ ON/OFF & Step Response ############
pause = True
def pause_animation():
    global pause
    if pause:
        ani.event_source.stop()
        pause = False
    else:
        ani.event_source.start()
        pause = True

def run_step_response():
    global pause
    if pause:
        ani.event_source.stop()
        pause = False
    
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

    try:
        dc_input_val = float(val1.get())
    except ValueError:
        dc_input_val = 0.0

    step_window = tkinter.Toplevel(root)
    step_window.title("Step Response Analysis")
    step_window.geometry("800x500")

    fig_step, ax_step = plt.subplots(figsize=(8, 5))
    fig_step.tight_layout(pad=3.0)

    ax_step.plot(x, y, label="Output Signal (Oscilloscope)", color='blue', linewidth=1.5)
    ax_step.axhline(y=dc_input_val, color='red', linestyle='--', linewidth=2, label=f"DC Supply Input ({dc_input_val} V)")

    ax_step.set_xlabel("Time (s)", fontsize=14)
    ax_step.set_ylabel("Voltage (V)", fontsize=14)
    ax_step.set_title("Input vs Output: Step Response", fontsize=16)
    ax_step.legend(loc='lower right', fontsize=12)
    ax_step.grid(True)

    canvas_step = FigureCanvasTkAgg(fig_step, master=step_window)
    canvas_step.get_tk_widget().pack(fill='both', expand=True)
    canvas_step.draw()


main_frame = tkinter.Frame(root)
main_frame.pack(side='top', fill='both', expand=True)

fm_ONOFF = tkinter.Frame(main_frame)
tkinter.Label(fm_ONOFF, text='Oscilloscope', font=("Arial Bold", 18)).pack(side=tkinter.LEFT)
button_run = tkinter.Button(fm_ONOFF, text="ON/OFF", command=pause_animation, font=('Arial Bold', 14), bg="yellow", fg="black")
button_run.pack(side=tkinter.LEFT)

button_step = tkinter.Button(fm_ONOFF, text="Step Analysis", command=run_step_response, font=('Arial Bold', 14), bg="cyan", fg="black")
button_step.pack(side=tkinter.LEFT, padx=5)

button_quit = tkinter.Button(fm_ONOFF, text="Quit", command=root.quit, font=('Arial Bold', 14), bg="red", fg="black")
button_quit.pack(side=tkinter.LEFT)
fm_ONOFF.pack(side=tkinter.LEFT, padx=10, pady=10)

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


### Create a wrapper frame for the right side so we can stack things vertically
fm_dc_container = tkinter.Frame(main_frame)
fm_dc_container.pack(side=tkinter.RIGHT, padx=10, pady=10)

fm_ch1 = tkinter.Frame(fm_dc_container)
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
fm_ch1.pack(side=tkinter.TOP)

### UPDATED: Frame and Labels to display the live DC Readings (Black color, aligned margins)
fm_readings = tkinter.Frame(fm_dc_container)

lbl_read_volt = tkinter.Label(fm_readings, text="Read V: -- V", font=("Arial Bold", 14), fg="black")
lbl_read_volt.pack(side=tkinter.LEFT, padx=10)

lbl_read_curr = tkinter.Label(fm_readings, text="Read I: -- A", font=("Arial Bold", 14), fg="black")
lbl_read_curr.pack(side=tkinter.LEFT, padx=10)

lbl_read_pwr = tkinter.Label(fm_readings, text="Read P: -- W", font=("Arial Bold", 14), fg="black")
lbl_read_pwr.pack(side=tkinter.LEFT, padx=10)

fm_readings.pack(side=tkinter.TOP, pady=8)


### Background function to poll the DC supply for voltage and current
def update_dc_readings():
    try:
        DC.write("INSTrument:NSELect 1") # Ensure Ch1 is selected
        v = float(DC.query("MEASure:VOLTage?"))
        i = float(DC.query("MEASure:CURRent?"))
        p = v * i  # Calculate Power
        
        lbl_read_volt.config(text=f"Read V: {v:.2f} V")
        lbl_read_curr.config(text=f"Read I: {i:.3f} A")
        lbl_read_pwr.config(text=f"Read P: {p:.3f} W")
    except Exception:
        # If communication is busy/fails, just ignore and try again next cycle
        pass
    
    # Schedule this function to run again in 500 milliseconds
    root.after(500, update_dc_readings)


def on_closing():
    scope.close()
    DC.close()
    root.quit()

root.protocol("WM_DELETE_WINDOW", on_closing)

# Start the background polling loop right before opening the UI
update_dc_readings()

tkinter.mainloop()