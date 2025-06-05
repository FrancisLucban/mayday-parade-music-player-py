import customtkinter as ctk
from tkinter import ttk
from pypresence import Presence
import pygame, os, sys, random, time, pyglet

from PIL import Image, ImageTk
from mutagen.flac import FLAC

# Initialize pygame mixer
pygame.mixer.init()

# Volume level constant
DEFAULT_VOL = 10

# Initialization of variables used when playing a song
song_number = 0
song_length = 0
current_song_name = None
current_assets = None
current_time = 0
filename = ""

# =========================================== DISCORD RPC ===========================================
client_id = "insert client id"
presence = Presence(client_id)
presence.connect()


# Initialization of flags
is_first_song = True  # Flag to check if it's the first song loaded
if_playing = False # Flag to check if current song is playing
is_paused = False # Flag to check if current song is paused
is_muted = False # Flag to check if muted
is_marquee_activated = False # Flag to check if marquee is on
is_black_lines_activated = False # Flag to check if "Black Lines" album is available

# After_id for playing_time function from getting called repeatedly
playing_time_active = None 

# Dynamic Pathing
if getattr(sys, 'frozen', False):
    # If running as a bundle (PyInstaller creates a temporary directory in sys._MEIPASS)
    base_path = sys._MEIPASS
else:
    # If running in a normal Python environment
    base_path = os.path.dirname(os.path.abspath(__file__))



# ===================================================== FONT INIT =====================================================
# Load multiple fonts
ls_black_path = os.path.join(base_path, 'fonts', 'LeagueSpartan-Black.ttf')
ls_extraBold_path = os.path.join(base_path, 'fonts', 'LeagueSpartan-ExtraBold.ttf')
ls_regular_path = os.path.join(base_path, 'fonts', 'LeagueSpartan-Regular.ttf')

pyglet.font.add_file(ls_black_path)
pyglet.font.add_file(ls_extraBold_path)
pyglet.font.add_file(ls_regular_path)

# Create multiple font styles
ls_black = ("League Spartan Black", 28)
ls_extraBold = ("League Spartan ExtraBold", 22)
ls_regular_album_title = ("League Spartan Regular", 15)
ls_regular_time = ("League Spartan Regular", 13)
ls_regular_version = ("League Spartan Regular", 12)


# ===================================================== FUNCTIONS =====================================================

# ---------------------------- Title Configuration Functions ----------------------------

def remove_characters_in_title(title):
    global song_number
    title = title.replace("[","").replace("]","")
    if "\"" in title:
        title = title.replace("\"","", 2)
    
    elif "\'" in title:
        title = title.replace("\'","", 2)

    if song_number in (2, 3, 6): # weird non breaking space (\xa0)
        title = title[:-4]

    return title


def song_title_configuration(song_name):

    global current_song_name, is_marquee_activated
    current_song_name = remove_characters_in_title(song_name)
    root.title(f"Now Playing {current_song_name}")

    if len(current_song_name) >= 63: #66
        is_marquee_activated = True
        current_song_name = current_song_name + "        "
        scroll_text()

    else:
        is_marquee_activated = False
        song_title.configure(text=current_song_name)
    
    #get_song_name(current_song_name)
    #update_presence(current_song_name)

def scroll_text():
    global current_song_name, is_marquee_activated, if_playing
    if is_marquee_activated and if_playing:
        current_song_name = current_song_name[1:] + current_song_name[0]
        song_title.configure(text=current_song_name)
        song_title.after(200, scroll_text)


# ---------------------------- SONG CHOOSER FUNCTION ----------------------------

def song_chooser():
    if is_black_lines_activated:
        rand_num = random.randrange(1,101)
        play_random_song(rand_num)
    
    else:
        rand_num = random.randrange(1,89)
        play_random_song(rand_num)


# ---------------------------- BLACK LINES ACTIVATION FUNCTION ----------------------------

def black_lines_activation():
    global is_black_lines_activated
    
    if is_black_lines_activated: # Revert to original design
        black_lines_button.configure(text="NO BLACK LINES ALBUM! :(")
        is_black_lines_activated = False
        play_random_song(random.randrange(1,89))

    else: # Change design when pressed
        black_lines_button.configure(text="BLACK LINES AVAILABLE :)")
        is_black_lines_activated = True
        play_random_song(random.randrange(89,101))


# ---------------------------- PLAY RANDOM SONG ----------------------------

def play_random_song(num):
    global if_playing, is_paused, song_number, is_first_song, song_length, filename, current_time, playing_time_active

    # Stops previous song to prevent overlapping of songs
    stop_song()

    # Cancel any previous scheduled after calls
    if playing_time_active is not None:
        playing_time_label.after_cancel(playing_time_active)
        playing_time_active = None

    song_number = num
    if_playing = True
    is_paused = False

    filename = os.path.join(base_path, "mp/", str(num) + ".flac")

    # Load and play the selected song
    pygame.mixer.music.load(filename)
    pygame.mixer.music.play()

    # Converts song file into a readable FLAC file to access metadata
    filename_flac = FLAC(filename)

    # Length of the current song and configuring max value of the slider equal to the song's length
    song_length = int(filename_flac.info.length)

    # Resets current time value every time a new song is played
    current_time = 0

    # Updates current time of the song
    playing_time()

    # Changes album image of the song
    change_album_image(num)

    # Configures Title of the Song
    title = str(filename_flac.get("title"))
    title_caps = title.upper()
    song_title_configuration(title_caps)

    if is_first_song:
        volume_slider.set(DEFAULT_VOL)
        update_volume(DEFAULT_VOL)  # Set the initial volume level
        is_first_song = False  # After loading the first song, set this to False
    
    # Updates activity on discord
    update_presence(current_song_name, current_assets)


# ---------------------------- CHECK END MUSIC FUNCTION ----------------------------

def check_music_end():
    if if_playing and not is_paused and not pygame.mixer.music.get_busy():  # Check if music is not busy (stopped)
        song_chooser()

    # Check every 100ms
    root.after(1000, check_music_end)


# ---------------------------- STOP SONG ----------------------------
def stop_song():
    global if_playing, is_paused, song_number, song_length, current_time, filename, current_song_name, current_assets

    if_playing = False
    is_paused = False
    song_number = 0
    song_length = 0
    current_time = 0
    current_song_name = None
    current_assets = None
    filename = ""

    update_presence(current_song_name, current_assets)

    # Stop Function
    pygame.mixer.music.stop()
    pygame.mixer.music.unload()

    # Reset every widget to its original state
    progress_slider.config(value=0)
    root.title("Mayday Parade Music Player by Lightsailor")
    album_cover_label.configure(image=album_cover_image)
    song_title.configure(text=" ")
    album_title.configure(text=" ")
    playing_time_label.configure(text="--:--")
    song_length_label.configure(text="--:--")
    
    # Reset the pause button to its original state
    pause_button.configure(image=pause_image, command=toggle_play_pause)
    hover_effects_play(pause_button, pause_image, pause_hovered)

# ---------------------------- PLAY/UNPAUSE SONG ----------------------------

def toggle_play_pause():
    global if_playing, is_paused, toggled_pause

    if if_playing:
        if is_paused:
            # Unpause the song
            is_paused = False
            pygame.mixer.music.unpause()
            pause_button.configure(image=pause_image, command=toggle_play_pause)
            hover_effects_play(pause_button, pause_image, pause_hovered)
        else:
            # Pause the song
            is_paused = True
            pygame.mixer.music.pause()
            pause_button.configure(image=play_image, command=toggle_play_pause)
            hover_effects_play(pause_button, play_image, play_hovered)


# ---------------------------- PREVIOUS SONG ----------------------------
def previous_song(song_num):
    if not if_playing:
        return

    if pygame.mixer.music.get_pos() / 1000 > 2:
        play_random_song(song_num)
        return

    last_song = 100 if is_black_lines_activated else 88
    play_random_song(last_song if song_num == 1 else song_num - 1)


# ---------------------------- NEXT SONG ----------------------------
def next_song(song_num):
    if not if_playing:
        return

    last_song = 100 if is_black_lines_activated else 88
    play_random_song(1 if song_num == last_song else song_num + 1)


# ---------------------------- CHANGE ALBUM IMAGE ----------------------------
def change_album_image(num):
    # Define mappings for image paths and album titles
    global current_assets
    album_data = [
        (range(1, 7), "images/ep1.jpg", "From the EP Tales Told by Dead Friends (2006)", "ep1"),
        ([7], "images/ep1.jpg", "From the EP Tales Told by Dead Friends Anniversary Edition (2016)", "ep1"),
        (range(8, 20), "images/album1.jpg", "From the album A Lesson in Romantics (2007)", "album1"),
        (range(20, 31), "images/album2.jpg", "From the album Anywhere but Here (2009)", "album2"),
        (range(31, 37), "images/ep2.jpg", "From the EP Valdosta EP (2011)", "ep2"),
        (range(37, 49), "images/album3.jpg", "From the album Mayday Parade (2011)", "album3"),
        (range(49, 61), "images/album4.jpg", "From the album Monsters in the Closet (2013)", "album4"),
        (range(61, 74), "images/album5.jpg", "From the album Sunnyland (2018)", "album5"),
        (range(74, 77), "images/ep3.jpg", "From the EP Out Of Here (2020)", "ep3"),
        (range(77, 89), "images/album6.jpg", "From the album What it Means to Fall Apart (2021)", "album6"),
    ]

    # Default image and title
    image_path = "images/black_lines.jpg"
    album_text = "From the album Black Lines (2015)"
    rp_assets = "black_lines"

    # Find the corresponding image and title based on num
    for num_range, img, title, icons in album_data:
        if num in num_range:
            image_path = img
            album_text = title
            rp_assets = icons
            break

    # Load and configure the image and text
    image = Image.open(os.path.join(base_path, image_path)).resize((300, 300))
    image = ImageTk.PhotoImage(image)
    album_title.configure(text=album_text)
    album_cover_label.configure(image=image)

    current_assets = rp_assets

# ---------------------------- UPDATE VOLUME ----------------------------
def update_volume(vol):
    global is_muted

    #if pygame.mixer.music.get_busy():
    pygame.mixer.music.set_volume(float(vol) / 100)  # Adjust the volume (scaled 0-100)

    vol = float(vol)
    if 0.1 <= vol <= 15.0:
        volume_slider.configure(fg_color="#444444", progress_color="lime green", 
                                button_color="lime green", button_hover_color="green")  # Low volume
        volume_icon_button.configure(image=volume_icon_converted)
        is_muted = False

    elif 20.0 <= vol <= 30.0:
        volume_slider.configure(fg_color="#444444", progress_color="yellow", 
                                button_color="yellow", button_hover_color="#969608")  # Medium volume
        volume_icon_button.configure(image=volume_icon_converted)
        is_muted = False

    elif 35.0 <= vol <= 50.0:
        volume_slider.configure(fg_color="#444444", progress_color="#FF474C", 
                                button_color="#FF474C", button_hover_color="red")  # High volume
        volume_icon_button.configure(image=volume_icon_converted)
        is_muted = False

    elif vol == 0:
        volume_slider.configure(fg_color="#444444", progress_color="lime green", 
                                button_color="lime green", button_hover_color="green")
        volume_icon_button.configure(image=volume_icon_muted_converted)
        volume_slider.set(0)
        is_muted = True

# ---------------------------- TOGGLE MUTE ----------------------------

def toggle_mute():
    global is_muted

    if is_muted:
        update_volume(DEFAULT_VOL)
        volume_slider.set(DEFAULT_VOL)
        is_muted = False
    
    else:
        update_volume(0)
        volume_slider.set(0)
        is_muted = True


# ---------------------------- HOVER EFFECTS FOR BUTTONS ----------------------------

def hover_effects(button, hovered):
    if button == play_random_song_button:
        def on_enter(e):
            button.configure(image=hovered)  # Change image while hovered

        def on_leave(e):
            button.configure(image=play_random_song_image) # Revert to original image after leaving

    elif button == previous_button:
        def on_enter(e):
            button.configure(image=hovered)  

        def on_leave(e):
            button.configure(image=previous_image)

    elif button == stop_button:
        def on_enter(e):
            button.configure(image=hovered)

        def on_leave(e):
            button.configure(image=stop_image)

    elif button == next_button:
        def on_enter(e):
            button.configure(image=hovered)

        def on_leave(e):
            button.configure(image=next_image)

    button.bind("<Enter>", on_enter)
    button.bind("<Leave>", on_leave)

# ---------------------------- HOVER EFFECTS FOR PAUSE/PLAY BUTTON ----------------------------

def hover_effects_play(button, original_image, hovered_image):
    def on_enter(e):
        button.configure(image=hovered_image)  # Change image while hovered

    def on_leave(e):
        button.configure(image=original_image)  # Revert to original image after leaving

    button.bind("<Enter>", on_enter)
    button.bind("<Leave>", on_leave)


# ---------------------------- SEEK SONG ----------------------------
def seek_song(e):
    pygame.mixer.music.set_pos(int(progress_slider.get()))


# ---------------------------- PLAYING TIME FUNCTION ----------------------------
def playing_time():
    global song_length, current_time, playing_time_active, playing_time_count

    # Cancel any previous scheduled after calls
    if playing_time_active is not None:
        playing_time_label.after_cancel(playing_time_active)
        playing_time_active = None

    current_time = pygame.mixer.music.get_pos()/1000
    converted_current_time = time.strftime('%M:%S', time.gmtime(current_time))
    converted_song_length = time.strftime('%M:%S', time.gmtime(song_length))

    current_time +=1
	
    if int(progress_slider.get()) == int(song_length):
        playing_time_label.configure(text=converted_song_length)
        song_length_label.configure(text=converted_song_length)
        #progress_slider.configure(value=0)
        
    elif is_paused:
        pass
    
    elif int(progress_slider.get()) == int(current_time):
		# Update Slider To position
        slider_position = int(song_length)
        progress_slider.config(to=slider_position, value=int(current_time))
    
    else:
		# Update Slider To position
        slider_position = int(song_length)
        progress_slider.config(to=slider_position, value=int(progress_slider.get()))
		
		# convert to time format
        converted_current_time = time.strftime('%M:%S', time.gmtime(int(progress_slider.get())))

		# Output time to status bar
        playing_time_label.configure(text=converted_current_time)
        song_length_label.configure(text=converted_song_length)

		# Move this thing along by one second
        next_time = int(progress_slider.get()) + 1
        progress_slider.config(value=next_time)

    # playing_time_count += 1
    # version_label.configure(text=f"Playing Time Count: {playing_time_count}")
    playing_time_active = playing_time_label.after(1000, playing_time)


def update_presence(song_name, album_image):
    presence.update(
        start=int(time.time()),
        details=f"Listening to: {song_name}",
        small_image="icon",
        large_image=album_image
    )

# Function to periodically update presence
def periodic_update():
    global current_song_name, current_assets
    update_presence(current_song_name, current_assets)
    root.after(15000, periodic_update)  # Schedule next update in 15 seconds




# ===================================================== TKINTER =====================================================

root = ctk.CTk()
root.title("Mayday Parade Music Player by Lightsailor")
root.iconbitmap(os.path.join(base_path, "images/icon.ico"))
root.geometry("800x650")
root.wm_minsize(800, 650)
#root.resizable(width=False, height=False)
ctk.set_appearance_mode("dark")

# ============== MAIN LOGO FRAME ==============

main_logo_frame = ctk.CTkFrame(root, fg_color="#B7271E") #ce3329
main_logo_frame.pack(fill=ctk.BOTH)

logo = Image.open(os.path.join(base_path, "images/title.png")).resize((308, 144))
logo = ImageTk.PhotoImage(logo)

img_display = ctk.CTkLabel(main_logo_frame, image=logo, fg_color="transparent", text=" ")
img_display.grid(pady=20, padx=15, row=0, column=0)

black_lines_button = ctk.CTkButton(main_logo_frame, text="NO BLACK LINES ALBUM! :(", 
                               font=ls_black, fg_color="transparent", 
                               hover=False, command=black_lines_activation)
black_lines_button.grid(pady=20, padx=55, row=0, column=1)


# ============== MUSIC PLAYER FRAME ==============

# ---------------- COLUMN 0 ----------------

# Frame declaration
music_player_frame = ctk.CTkFrame(root, fg_color="transparent")
music_player_frame.pack(pady=40, padx=40, expand=True)
#music_player_frame.pack_propagate(False)

# Album Cover Image
album_cover_image = Image.open(os.path.join(base_path, "images/album_cover_placeholder.png")).resize((300, 300))
album_cover_image = ImageTk.PhotoImage(album_cover_image)

# Album Cover Label
album_cover_label = ctk.CTkLabel(music_player_frame, image=album_cover_image, fg_color="transparent", text=" ")
album_cover_label.grid(row=0, column=0, rowspan=4, sticky="w")

# Song title
song_title = ctk.CTkLabel(music_player_frame, text=" ", font=ls_extraBold)
song_title.grid(row=4, column=0, columnspan=400, sticky="nw")

# Album title
album_title = ctk.CTkLabel(music_player_frame, text=" ", font=ls_regular_album_title)
album_title.grid(row=5, column=0, columnspan=2, sticky="nw")


# ---------------- COLUMN 1  ----------------

# ------- Random song button ------- (ROW 0)

play_random_song_image = Image.open(os.path.join(base_path, "images/play_random.png")).resize((227, 93)) #324, 133
play_random_song_image = ImageTk.PhotoImage(play_random_song_image)

play_random_song_hovered = Image.open(os.path.join(base_path, "images/play_random_hovered.png")).resize((227, 93)) #324, 133
play_random_song_hovered = ImageTk.PhotoImage(play_random_song_hovered)

play_random_song_button = ctk.CTkButton(music_player_frame, image=play_random_song_image, 
                                    fg_color="transparent", command=song_chooser, 
                                    text=" ", hover=False) 
play_random_song_button.grid(row=0, column=1, padx=60)
 


# ------- Seek Duration Scale ------- (ROW 1)
seek_duration_frame = ctk.CTkFrame(music_player_frame, fg_color="transparent")
seek_duration_frame.grid(row=1, column=1)

# Playing Time
playing_time_label = ctk.CTkLabel(seek_duration_frame, text="--:--", font=ls_regular_time, fg_color="transparent")
playing_time_label.grid(row=0, column=0, padx=10)

# Progress Bar
progress_slider = ttk.Scale(seek_duration_frame, from_=0, to=100, value=0, length=250,
                            command=seek_song)
progress_slider.grid(row=0, column=1, padx=0)

# Song Length
song_length_label = ctk.CTkLabel(seek_duration_frame, text="--:--", font=ls_regular_time, fg_color="transparent")
song_length_label.grid(row=0, column=2, padx=10)


# ------- Control Buttons ------- (ROW 2)
# FRAME
control_button_frame = ctk.CTkFrame(music_player_frame, fg_color="transparent")
control_button_frame.grid(row=2, column=1)

# Previous Button
previous_image = Image.open(os.path.join(base_path, "images/previous.png")).resize((20, 20))
previous_image = ImageTk.PhotoImage(previous_image)

previous_hovered = Image.open(os.path.join(base_path, "images/previous_hovered.png")).resize((20, 20))
previous_hovered = ImageTk.PhotoImage(previous_hovered)

previous_button = ctk.CTkButton(control_button_frame, image=previous_image, width=32,
                        fg_color="transparent", command=lambda: previous_song(song_number),
                        text=" ", hover=False)
previous_button.grid(row=0,column=0, padx=0)


# Play/Pause Button
play_image = Image.open(os.path.join(base_path, "images/play.png")).resize((28, 28))
play_image = ImageTk.PhotoImage(play_image)

play_hovered = Image.open(os.path.join(base_path, "images/play_hovered.png")).resize((28, 28))
play_hovered = ImageTk.PhotoImage(play_hovered)

pause_image = Image.open(os.path.join(base_path, "images/pause.png")).resize((32, 32))
pause_image = ImageTk.PhotoImage(pause_image)

pause_hovered = Image.open(os.path.join(base_path, "images/pause_hovered.png")).resize((32, 32))
pause_hovered = ImageTk.PhotoImage(pause_hovered)

pause_button = ctk.CTkButton(control_button_frame, image=pause_image, width=32,
                        fg_color="transparent", command=lambda: toggle_play_pause,
                        text=" ", hover=False)
pause_button.grid(row=0,column=2, padx=0)


# Stop Button
stop_image = Image.open(os.path.join(base_path, "images/stop.png")).resize((32, 32))
stop_image = ImageTk.PhotoImage(stop_image)

stop_hovered = Image.open(os.path.join(base_path, "images/stop_hovered.png")).resize((32, 32))
stop_hovered = ImageTk.PhotoImage(stop_hovered)

stop_button = ctk.CTkButton(control_button_frame, image=stop_image, width=32,
                        fg_color="transparent", command=stop_song,
                        text=" ", hover=False)
stop_button.grid(row=0, column=3, padx=0)


# Next Button
next_image = Image.open(os.path.join(base_path, "images/next.png")).resize((20, 20))
next_image = ImageTk.PhotoImage(next_image)

next_hovered = Image.open(os.path.join(base_path, "images/next_hovered.png")).resize((20, 20))
next_hovered = ImageTk.PhotoImage(next_hovered)

next_button = ctk.CTkButton(control_button_frame, image=next_image, width=32,
                        fg_color="transparent", command= lambda: next_song(song_number),
                        text=" ", hover=False)
next_button.grid(row=0, column=4, padx=0)


# ------- Volume Slider ------- (ROW 3)
# FRAME
volume_slider_frame = ctk.CTkFrame(music_player_frame, fg_color="transparent")
volume_slider_frame.grid(row=3, column=1)

volume_icon = Image.open(os.path.join(base_path, "images/volume.png")).resize((30,30))
volume_icon_converted = ImageTk.PhotoImage(volume_icon)

volume_icon_muted = Image.open(os.path.join(base_path, "images/muted.png")).resize((30,30))
volume_icon_muted_converted = ImageTk.PhotoImage(volume_icon_muted)

volume_icon_button = ctk.CTkButton(volume_slider_frame, image=volume_icon_converted, fg_color="transparent", 
                                   text="", width=30, hover=False, command=toggle_mute)
volume_icon_button.grid(row=0, column=0, padx=0)

volume_slider = ctk.CTkSlider(volume_slider_frame, from_=0, to=50, number_of_steps=50, command=update_volume, 
                              progress_color="lime green", button_color="lime green", button_hover_color="green")
volume_slider.set(DEFAULT_VOL)
volume_slider.grid(row=0, column=1, padx=5)


# ============== VERSION LABEL ==============
version_label = ctk.CTkLabel(root, text="Version 1.3", font=ls_regular_version)
version_label.pack(side=ctk.RIGHT, padx=10)


# ============== HOVER EFFECTS FOR BUTTONS ==============
hover_effects(play_random_song_button, play_random_song_hovered)
hover_effects(previous_button, previous_hovered)
hover_effects(stop_button, stop_hovered)
hover_effects(next_button, next_hovered)
hover_effects_play(pause_button, pause_image, pause_hovered)

# Start checking if music has ended
root.after(1000, check_music_end)
root.mainloop()