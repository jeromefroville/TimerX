# TimerX v1.1
# IMPORTS
import pyautogui

ver = "1.1"

import time
import tkinter
import webbrowser
from pathlib import Path
from platform import system
from threading import Thread
from tkinter import Frame, Tk
from tkinter.constants import DISABLED, END, LEFT, NORMAL
from tkinter.filedialog import askopenfile

import darkdetect
import sv_ttk
from playsound import playsound

if system() == "Windows":
    from win10toast_click import ToastNotifier
    import ctypes

from utils import *

if not Path("config.json").exists():
    createConfig()

config = loadConfig(ver)

theme = config["theme"]
if config["theme"] == "System":
    if darkdetect.isDark():
        theme = "Dark"
    else:
        theme = "Light"

# TKINTER WINDOW
app = Tk()
app.title("")
app.minsize(width=50, height=50)
app.wm_geometry("182x120")

sv_ttk.set_theme(theme.lower())
bg_color = ttk.Style().lookup(".", "background")


# SYSTEM CODE
def seticon(win):
    try:
        if system() == "darwin":
            win.iconbitmap("./assets/logo_new.icns")
        elif system() == "Windows":
            win.iconbitmap("./assets/logo_new.ico")
        else:
            logo_img = PhotoImage(file="./assets/logo_new.png")
            win.iconphoto(False, logo_img)
    except tkinter.TclError:
        try:
            win.iconphoto("assets/logo.ico")
        except tkinter.TclError:
            pass


def fullredraw(e):
    global prev_state
    print(prev_state)
    if prev_state == "zoomed":
        print("this")
        true_value = ctypes.c_int(1)
        ctypes.windll.dwmapi.DwmSetWindowAttribute(
            app.wm_frame(), 3, ctypes.byref(true_value), ctypes.sizeof(true_value)
        )

        app.iconify()
        app.deiconify()

        false_value = ctypes.c_int(0)
        ctypes.windll.dwmapi.DwmSetWindowAttribute(
            app.wm_frame(), 3, ctypes.byref(false_value), ctypes.sizeof(false_value)
        )

    prev_state = app.state()


seticon(app)

# VARIABLES
app_on = True

timer_on = False
timer_paused = False
timer_stopped = False

timer_seconds = int(config["default_seconds"])
timer_minutes = int(config["default_minutes"])
timer_hours = int(config["default_hours"])


# FUNCTIONS
def playBuzzer():
    playsound(config["sound_path"])


def stopTimerAndSetNewValue(hours: int, minutes: int, seconds: int):
    global hours_left, minutes_left, seconds_left, timer_seconds, timer_minutes, timer_hours, timer_stopped

    config["default_seconds"] = seconds
    config["default_minutes"] = minutes
    config["default_hours"] = hours

    saveConfig(config)

    timer_hours = hours
    timer_minutes = minutes
    timer_seconds = seconds

    hours_left = timer_hours
    minutes_left = timer_minutes
    seconds_left = timer_seconds

    if timer_on:
        timer_stopped = True

    time_display.configure(text=f"{hours_left:02d} : {minutes_left:02d} : {seconds_left:02d}")


def buttonPressedReset(*_):
    stopTimerAndSetNewValue(int(config["default_hours"]), int(config["default_minutes"]), int(config["default_seconds"]))


def buttonPressedFast1(*_):
    stopTimerAndSetNewValue(0, 5, 0)


def buttonPressedFast2(*_):
    stopTimerAndSetNewValue(0, 25, 0)


def buttonPressedFast3(*_):
    stopTimerAndSetNewValue(0, 10, 0)


def buttonPressedFast4(*_):
    stopTimerAndSetNewValue(0, 15, 0)


def buttonPressedStartStop(*_):
    global timer_on, timer_hours, timer_minutes, timer_seconds, last_paused, timer_stopped, hours_left, minutes_left, seconds_left

    if timer_on:
        timer_on = False
        timer_stopped = True
        timer_hours = hours_left
        timer_minutes = minutes_left
        timer_seconds = seconds_left
        reset_button.configure(state=NORMAL)
        edit_timer_button.configure(state=NORMAL)
        fast1_button.configure(state=NORMAL)
        fast2_button.configure(state=NORMAL)
        fast3_button.configure(state=NORMAL)
        fast4_button.configure(state=NORMAL)
        play_button.configure(text="Play")
    else:
        play_button.configure(text="Stop")
        hours_left = timer_hours
        minutes_left = timer_minutes
        seconds_left = timer_seconds
        edit_timer_button.configure(state=DISABLED)
        reset_button.configure(state=DISABLED)
        fast1_button.configure(state=DISABLED)
        fast2_button.configure(state=DISABLED)
        fast3_button.configure(state=DISABLED)
        fast4_button.configure(state=DISABLED)
        timer_thread = Thread(target=runTimer, daemon=True)
        timer_thread.start()
        anti_screen_locker_thread = Thread(target=runAntiScreenLocker, daemon=True)
        anti_screen_locker_thread.start()


def runAntiScreenLocker():
    while True:
        if not timer_on:
            break;
        pyautogui.move(1, 1)
        time.sleep(30)
        pyautogui.move(-1, -1)
        time.sleep(30)


def saveTimer(secs, mins, hours, manager_app_window):
    global timer_seconds, timer_minutes, timer_hours, hours_left, minutes_left, seconds_left, config

    timer_seconds = int(secs)
    timer_minutes = int(mins)
    timer_hours = int(hours)

    hours_left = timer_hours
    minutes_left = timer_minutes
    seconds_left = timer_seconds

    time_selected_display.configure(
        text=f"{hours_left:02d} Hours, {minutes_left:02d} Minutes, {seconds_left:02d} Seconds"
    )
    time_display.configure(text=f"{hours_left:02d} : {minutes_left:02d} : {seconds_left:02d}")

    config["default_seconds"] = timer_seconds
    config["default_minutes"] = timer_minutes
    config["default_hours"] = timer_hours

    saveConfig(config)

    if not manager_app_window == None:
        manager_app_window.destroy()


import subprocess


def sendmessage(summary, body):
    subprocess.Popen(['notify-send', "-t", "5000", summary, body])
    return


def showNotification():
    sendmessage("TimerX", "Time's up!")

    if system() == "Windows":
        notification = ToastNotifier()
        notification.show_toast(
            "TimerX",
            "Time's up!",
            icon_path="./assets/logo_new.ico",
            duration="None",
            threaded=True,
            callback_on_click=app.focus_force(),
        )


def runTimer():
    global timer_seconds, timer_minutes, timer_hours, timer_on, app, config, last_paused, seconds_left, minutes_left, hours_left, timer_stopped, time_display

    # timer_seconds = config["default_seconds"]
    # timer_minutes = config["default_minutes"]
    # timer_hours = config["default_hours"]

    timer_hours = hours_left
    timer_minutes = minutes_left
    timer_seconds = seconds_left

    # seconds_left = timer_seconds
    # minutes_left = timer_minutes
    # hours_left = timer_hours
    milliseconds_left = 99
    timer_on = True

    last_paused = time.time()

    while True:
        if timer_stopped:
            break;

        # if timer_on and not timer_paused:
        if timer_on:
            latest_time = time.time()

            time_to_subtract = round((latest_time - last_paused), 3)

            split_time = str(time_to_subtract).split(".")

            ty_res = time.gmtime(int(split_time[0]))
            formatted_time = time.strftime(f"%H:%M:%S:{split_time[1]}", ty_res)

            milliseconds_left -= int(split_time[1])
            split_fmt_time = formatted_time.split(":")
            hours_left = int(timer_hours) - int(split_fmt_time[0])
            minutes_left = int(timer_minutes) - int(split_fmt_time[1])
            seconds_left = int(timer_seconds) - int(split_fmt_time[2])

            if seconds_left < 0 and minutes_left == 0 and hours_left == 0:
                break

            if seconds_left < 0:
                subtract_secs = abs(seconds_left)
                seconds_left = 60 - subtract_secs
                minutes_left -= 1
            if minutes_left < 0:
                subtract_mins = abs(minutes_left)
                minutes_left = 60 - subtract_mins
                hours_left -= 1

            time_display.configure(
                text=f"{hours_left:02d} : {minutes_left:02d} : {seconds_left:02d}"
            )

    if not timer_stopped:
        if config["notify"]:
            showNotification()
        if config["sound"]:
            playBuzzer()
    timer_on = False
    timer_stopped = False
    play_button.config(text="Play")
    edit_timer_button.configure(state=NORMAL)

    time_display.configure(text=f"{config['default_hours']:02d} : {config['default_minutes']:02d} : {config['default_seconds']:02d}")



def setAlwaysOnTop():
    app.attributes("-topmost", config["ontop"])


setAlwaysOnTop()


# WINDOWS
def createManagerWindow(saveTimer, current_mins, current_secs, current_hrs):
    global manager_app_window, config

    manager_app_window = tkinter.Toplevel()
    manager_app_window.geometry("250x170")
    manager_app_window.title("Edit Timer")
    manager_app_window.wait_visibility()
    manager_app_window.attributes("-alpha", config["transperency"])
    manager_app_window.resizable(False, False)

    seticon(manager_app_window)

    # VALIDATION
    validate_command = manager_app_window.register(validate)

    # WINDOW FRAME
    manager_window = ttk.Frame(manager_app_window)
    manager_window.pack(fill="both", expand=True)

    timer_hr_label = ttk.Label(manager_window, text="Hours: ")
    timer_hr_label.place(x=17, y=17)
    timer_hr_input = ttk.Entry(
        manager_window, validate="key", validatecommand=(validate_command, "%P")
    )
    timer_hr_input.place(x=65, y=10)
    timer_hr_input.insert(1, current_hrs)

    timer_min_label = ttk.Label(manager_window, text="Minutes: ")
    timer_min_label.place(x=13, y=57)
    timer_min_input = ttk.Entry(
        manager_window, validate="key", validatecommand=(validate_command, "%P")
    )
    timer_min_input.place(x=65, y=50)
    timer_min_input.insert(1, current_mins)

    timer_sec_label = ttk.Label(manager_window, text="Seconds: ")
    timer_sec_label.place(x=12, y=97)
    timer_sec_input = ttk.Entry(
        manager_window, validate="key", validatecommand=(validate_command, "%P")
    )
    timer_sec_input.place(x=65, y=90)
    timer_sec_input.insert(1, current_secs)

    ok_button = ttk.Button(
        manager_window,
        text="Ok!",
        command=lambda: saveTimer(
            timer_sec_input.get(),
            timer_min_input.get(),
            timer_hr_input.get(),
            manager_app_window,
        ),
        style="Accent.TButton",
    )
    ok_button.place(x=95, y=126)


def createSettingsWindow():
    global theme, config, sp

    settings_window = tkinter.Toplevel()
    settings_window.geometry("500x320")
    settings_window.title("Settings")
    settings_window.resizable(False, False)
    settings_window.wait_visibility()
    settings_window.attributes("-alpha", config["transperency"])

    seticon(settings_window)

    tabview = ttk.Notebook(settings_window)
    tabview.pack(fill="both", expand=True)

    tab_1 = ttk.Frame(tabview)
    tab_2 = ttk.Frame(tabview)
    tab_3 = ttk.Frame(tabview)
    tab_4 = ttk.Frame(tabview)

    tabview.add(tab_1, text="Appearence")
    tabview.add(tab_2, text="Notifications & Sound")
    tabview.add(tab_3, text="Timer Defaults")
    tabview.add(tab_4, text="About")

    theme_label = ttk.Label(
        tab_1,
        text="  Change theme of the app",
        image=theme_dark,
        compound=LEFT,
    )
    theme_label.place(x=23, y=23)

    transparency_label = ttk.Label(
        tab_1,
        text="  Adjust Transparency of the app",
        image=transparency_dark,
        compound=LEFT,
    )
    transparency_label.place(x=23, y=73)

    pin_label = ttk.Label(
        tab_1, text="  Keep app always on top", image=pin_dark, compound=LEFT
    )
    pin_label.place(x=23, y=123)

    speaker_label = ttk.Label(
        tab_2,
        text="  Play sound when timer ends",
        image=speaker_dark,
        compound=LEFT,
    )
    speaker_label.place(x=23, y=23)

    bell_label = ttk.Label(
        tab_2,
        text="  Show notification when timer ends",
        image=bell_dark,
        compound=LEFT,
    )
    bell_label.place(x=23, y=73)

    sound_path_label = ttk.Label(tab_2, text="Default Sound:").place(x=23, y=123)
    default_secs_label = ttk.Label(tab_3, text="    Default Seconds:").place(x=23, y=23)
    default_mins_label = ttk.Label(tab_3, text="    Default Minutes:").place(x=23, y=93)
    default_hours_label = ttk.Label(tab_3, text="    Default Hours:").place(x=23, y=163)

    logo_label = ttk.Label(tab_4, image=logo).place(x=50, y=30)
    TimerX_Label = ttk.Label(
        tab_4, text="TimerX", font=("Arial Rounded MT Bold", 50)
    ).place(x=210, y=40)
    version_Label = ttk.Label(
        tab_4, text=f"Version: {ver}", font=("Segoe UI", "20")
    ).place(x=220, y=120)

    github_btn = ttk.Button(
        tab_4,
        text=" Fork on Github",
        image=github_logo_dark,
        compound=LEFT,
        command=lambda: webbrowser.open("https://github.com/Futura-Py/TimerX"),
    )
    github_btn.place(x=50, y=200)

    website_btn = ttk.Button(
        tab_4,
        text=" Check out our Website!",
        image=globe_dark,
        compound=LEFT,
        command=lambda: webbrowser.open("https://Futura-Py.netlify.app/"),
    )
    website_btn.place(x=250, y=200)

    if theme == "Dark":
        theme_label.configure(image=theme_dark)
        transparency_label.configure(image=transparency_dark)
        speaker_label.configure(image=speaker_dark)
        bell_label.configure(image=bell_dark)
        pin_label.configure(image=pin_dark)
        github_btn.configure(image=github_logo_dark)
        website_btn.configure(image=globe_dark)
    else:
        theme_label.configure(image=theme_light)
        transparency_label.configure(image=transparency_light)
        speaker_label.configure(image=speaker_light)
        bell_label.configure(image=bell_light)
        pin_label.configure(image=pin_light)
        github_btn.configure(image=github_logo_light)
        website_btn.configure(image=globe_light)

    theme_combobox = ttk.Spinbox(
        tab_1,
        state="readonly",
        values=("Dark", "Light", "System"),
        wrap=True,
    )
    theme_combobox.place(x=275, y=20)
    theme_combobox.set(config["theme"])

    def slider_changed(value):
        value = float(value) / 100
        settings_window.attributes("-alpha", value)
        app.attributes("-alpha", value)

    slider = ttk.Scale(
        tab_1,
        from_=40,
        to=99,
        orient="horizontal",
        command=slider_changed,
    )
    slider.set(float(config["transperency"]) * 100)
    slider.place(x=325, y=75)

    sound_button = ttk.Checkbutton(tab_2, style="Switch.TCheckbutton")
    if config["sound"]:
        sound_button.state(["!alternate", "selected"])
    else:
        sound_button.state(["!alternate"])
    sound_button.place(x=360, y=25)

    notify_button = ttk.Checkbutton(tab_2, style="Switch.TCheckbutton")
    if config["notify"]:
        notify_button.state(["!alternate", "selected"])
    else:
        notify_button.state(["!alternate"])
    notify_button.place(x=360, y=75)

    ontop_button = ttk.Checkbutton(tab_1, style="Switch.TCheckbutton")
    if config["ontop"]:
        ontop_button.state(["!alternate", "selected"])
    else:
        ontop_button.state(["!alternate"])
    ontop_button.place(x=360, y=125)

    def browse():
        filedialog = askopenfile(
            mode="r", filetypes=[("Audio Files", ["*.mp3", "*.wav"])]
        )
        if not filedialog == None:
            sound_path_entry.delete(0, END)
            sound_path_entry.insert(1, filedialog.name)

    sound_path_entry = ttk.Entry(tab_2, width=35)
    sound_path_entry.insert(1, config["sound_path"])
    sound_path_entry.place(x=130, y=115)
    spe_error_lbl = tkinter.Label(tab_2, fg="red", font=("", 10), text="")
    spe_error_lbl.place(x=130, y=150)

    browse_btn = ttk.Button(tab_2, text="Browse", command=lambda: browse())
    browse_btn.place(x=410, y=115)

    default_secs_entry = ttk.Entry(tab_3)
    default_secs_entry.insert(1, config["default_seconds"])
    default_secs_entry.place(x=280, y=15)
    dse_error_lbl = tkinter.Label(tab_3, fg="red", font=("", 10), text="")
    dse_error_lbl.place(x=280, y=50)

    default_mins_entry = ttk.Entry(tab_3)
    default_mins_entry.insert(1, config["default_minutes"])
    default_mins_entry.place(x=280, y=85)
    dme_error_lbl = tkinter.Label(tab_3, fg="red", font=("", 10), text="")
    dme_error_lbl.place(x=280, y=120)

    default_hours_entry = ttk.Entry(tab_3)
    default_hours_entry.insert(1, config["default_hours"])
    default_hours_entry.place(x=280, y=155)
    dhe_error_lbl = tkinter.Label(tab_3, fg="red", font=("", 10), text="")
    dhe_error_lbl.place(x=280, y=190)

    def ApplyChanges():
        global theme

        config["theme"] = theme = theme_combobox.get()
        if theme == "System":
            if darkdetect.isDark():
                theme = "Dark"
            else:
                theme = "Light"

        config["transperency"] = float(slider.get()) / 100
        config["sound"] = sound_button.instate(["selected"])
        config["notify"] = notify_button.instate(["selected"])
        config["ontop"] = ontop_button.instate(["selected"])
        config["default_seconds"] = default_secs_entry.get()
        config["default_minutes"] = default_mins_entry.get()
        config["default_hours"] = default_hours_entry.get()
        config["sound_path"] = sp

        setAlwaysOnTop()

        saveTimer(
            config["default_seconds"],
            config["default_minutes"],
            config["default_hours"],
            None,
        )

        saveTimer(
            config["default_seconds"],
            config["default_minutes"],
            config["default_hours"],
            None,
        )

        saveConfig(config)

        sv_ttk.set_theme(theme.lower())

        if theme == "Dark":
            settings_btn.configure(image=settings_image_dark)
            time_display.configure(fg="white")
        else:
            settings_btn.configure(image=settings_image_light)
            time_display.configure(fg="black")

        settings_window.destroy()

    def VerifyEntrys():
        global sp

        def Error(reason, entry, label):
            if reason == "wv":
                entry.state(["invalid"])
                label.configure(text="Enter a number below 60")
            elif reason == "wv2":
                entry.state(["invalid"])
                label.configure(text="Enter a number below 24")
            elif reason == "not_int":
                entry.state(["invalid"])
                label.configure(text="Enter a number")
            elif reason == "wv-":
                entry.state(["invalid"])
                label.configure(text="Enter a number above 0")
            elif reason == "wv-2":
                entry.state(["invalid"])
                label.configure(text="Enter a number above or equal to 0")
            elif reason == "sound":
                entry.state(["invalid"])
                label.configure(text="This file doesnt exist.")

        validated = True

        try:
            void = int(default_secs_entry.get())
            if not void < 60:
                validated = False
                Error("wv", default_secs_entry, dse_error_lbl)
            # if not void > 0:
            #     validated = False
            #     Error("wv-", default_secs_entry, dse_error_lbl)
        except ValueError:
            Error("not_int", default_secs_entry, dse_error_lbl)
            validated = False

        try:
            void = int(default_mins_entry.get())
            if not void < 60:
                validated = False
                Error("wv", default_mins_entry, dme_error_lbl)
            if not void > -1:
                validated = False
                Error("wv-2", default_mins_entry, dme_error_lbl)
        except ValueError:
            Error("not_int", default_mins_entry, dme_error_lbl)
            validated = False

        try:
            void = int(default_hours_entry.get())
            if not void <= 24:
                validated = False
                Error("wv2", default_hours_entry, dhe_error_lbl)
            if not void > -1:
                validated = False
                Error("wv-2", default_hours_entry, dhe_error_lbl)
        except ValueError:
            Error("not_int", default_hours_entry, dhe_error_lbl)
            validated = False

        if validated and int(default_hours_entry.get()) == 0 and int(default_mins_entry.get()) == 0 and int(default_secs_entry.get()) == 0:
            validated = False
            Error("wv-", default_secs_entry, dse_error_lbl)

        sp = sound_path_entry.get()
        sp = sp.replace("\\", "/")

        if not Path(sp).exists():
            Error("sound", sound_path_entry, spe_error_lbl)
            validated = False

        if validated == True:
            ApplyChanges()

    for index in [tab_1, tab_2, tab_3]:
        ttk.Button(
            index,
            text="Apply Changes",
            command=lambda: VerifyEntrys(),
            style="Accent.TButton",
        ).place(x=250, y=230)

        ttk.Button(
            index, text="Cancel", command=lambda: settings_window.destroy()
        ).place(x=125, y=230)

    # if not system() == "Windows" or system() == "win":
    #     notify_button.configure(state=DISABLED)

    def reset_dse(e):
        default_secs_entry.state(["!invalid"])
        dse_error_lbl.configure(text="")

    def reset_dme(e):
        default_mins_entry.state(["!invalid"])
        dme_error_lbl.configure(text="")

    def reset_dhe(e):
        default_hours_entry.state(["!invalid"])
        dhe_error_lbl.configure(text="")

    def reset_spe(e):
        sound_path_entry.state(["!invalid"])
        spe_error_lbl.configure(text="")

    default_secs_entry.bind("<FocusOut>", reset_dse)
    default_secs_entry.bind("<FocusIn>", reset_dse)
    default_secs_entry.bind("<KeyRelease>", reset_dse)

    default_mins_entry.bind("<FocusOut>", reset_dme)
    default_mins_entry.bind("<FocusIn>", reset_dme)
    default_mins_entry.bind("<KeyRelease>", reset_dme)

    default_hours_entry.bind("<FocusOut>", reset_dhe)
    default_hours_entry.bind("<FocusIn>", reset_dhe)
    default_hours_entry.bind("<KeyRelease>", reset_dhe)

    sound_path_entry.bind("<FocusOut>", reset_spe)
    sound_path_entry.bind("<FocusIn>", reset_spe)
    sound_path_entry.bind("<KeyRelease>", reset_spe)


# KEYBINDS
app.bind("key-space", buttonPressedStartStop)

app.grid_columnconfigure(0, weight=1)
app.grid_columnconfigure(1, weight=1)
app.grid_columnconfigure(2, weight=1)
app.grid_columnconfigure(3, weight=1)
app.grid_rowconfigure(0, weight=1)
app.grid_rowconfigure(1, weight=100)
app.grid_rowconfigure(2, weight=1)
app.grid_rowconfigure(3, weight=1)
app.grid_columnconfigure(1, weight=1)

# IMAGES
settings_image_light = PhotoImage(file="./assets/images/light/settings.png")
settings_image_dark = PhotoImage(file="./assets/images/dark/settings.png")

# WINDOW FRAME
window = Frame(app)

# WINDOW ELEMENTS
time_selected_display = tkinter.Label(
    master=app,
    text=f"{timer_hours} Hours, {timer_minutes} Minutes, {timer_seconds} Seconds",
    font=("Segoe UI Variable", 10),
    fg="white",
)
time_selected_display.grid(row=0, column=0, columnspan=4)

time_display = tkinter.Label(
    master=app,
    text=f"{timer_hours:02d} : {timer_minutes:02d} : {timer_seconds:02d}",
    font=("Segoe UI Variable", 30),
    fg="white",
)
time_display.grid(row=1, column=0, columnspan=4)

play_button = ttk.Button(
    master=app,
    text="Play",
    command=buttonPressedStartStop,
    style="Accent.TButton",
    padding=1
)
play_button.grid(row=2, column=0)

reset_button = ttk.Button(
    master=app,
    text="Reset",
    command=buttonPressedReset,
    padding=1
)
reset_button.grid(row=2, column=2)

edit_timer_button = ttk.Button(
    master=app,
    text="Edit",
    command=lambda: createManagerWindow(
        saveTimer, timer_minutes, timer_seconds, timer_hours
    ),
    padding=1
)
edit_timer_button.grid(row=2, column=1)

settings_btn = ttk.Button(
    master=app,
    image=settings_image_dark,
    command=lambda: createSettingsWindow(),
    style="Toolbutton",
    padding=0
)
settings_btn.grid(row=2, column=3)

fast1_button = ttk.Button(
    master=app,
    text="5'",
    command=buttonPressedFast1,
    padding=1
)
fast1_button.grid(row=3, column=0)
fast2_button = ttk.Button(
    master=app,
    text="25'",
    command=buttonPressedFast2,
    padding=1
)
fast2_button.grid(row=3, column=1)
fast3_button = ttk.Button(
    master=app,
    text="10'",
    command=buttonPressedFast3,
    padding=1
)
fast3_button.grid(row=3, column=2)
fast4_button = ttk.Button(
    master=app,
    text="15'",
    command=buttonPressedFast4,
    padding=1
)
fast4_button.grid(row=3, column=3)


def sizechanged(e):
    # settings_btn.place(x=5, y=app.winfo_height() - 45)

    time_selected_display.configure(font=("Segoe UI Variable", int(app.winfo_width() / 40)))
    time_display.configure(font=("Segoe UI Variable", int(app.winfo_width() / 9)))

    # play_button.configure(width=int(app.winfo_width() / 15))
    # edit_timer_button.configure(width=int(app.winfo_width() / 15))
    play_button.configure(width=int(app.winfo_width() / 30))
    edit_timer_button.configure(width=int(app.winfo_width() / 30))
    reset_button.configure(width=int(app.winfo_width() / 30))
    fast1_button.configure(width=int(app.winfo_width() / 30))
    fast2_button.configure(width=int(app.winfo_width() / 30))
    fast3_button.configure(width=int(app.winfo_width() / 30))
    fast4_button.configure(width=int(app.winfo_width() / 30))


# LOAD IMAGES
theme_dark = PhotoImage(file="./assets/images/dark/dark_theme.png")
theme_light = PhotoImage(file="./assets/images/light/dark_theme.png")

transparency_dark = PhotoImage(file="./assets/images/dark/transparency.png")
transparency_light = PhotoImage(file="./assets/images/light/transparency.png")

speaker_dark = PhotoImage(file="./assets/images/dark/speaker.png")
speaker_light = PhotoImage(file="./assets/images/light/speaker.png")

bell_dark = PhotoImage(file="./assets/images/dark/bell.png")
bell_light = PhotoImage(file="./assets/images/light/bell.png")

pin_dark = PhotoImage(file="./assets/images/dark/pin.png")
pin_light = PhotoImage(file="./assets/images/light/pin.png")

github_logo_dark = PhotoImage(file="./assets/images/dark/github.png")
github_logo_light = PhotoImage(file="./assets/images/light/github.png")

globe_dark = PhotoImage(file="./assets/images/dark/globe.png")
globe_light = PhotoImage(file="./assets/images/light/globe.png")

logo = PhotoImage(file="./assets/logo_new_150x150.png")

if theme == "Dark":
    settings_btn.configure(image=settings_image_dark)
elif theme == "Light":
    settings_btn.configure(image=settings_image_light)
    time_display.configure(fg="black")
    time_selected_display.configure(fg="black")

app.bind("<Configure>", sizechanged)

app.wait_visibility()
app.attributes("-alpha", config["transperency"])

# UPDATE
#app.after(500, Thread(target=checkForUpdates, args=(ver,)).start)

# TKINTER MAINLOOP
app.mainloop()
