import spotipy 
import os
import difflib
import csv
import json
from spotipy.oauth2 import SpotifyOAuth
import shutil

## CONSTANTS
SPOTIFY_SCOPE                       = "playlist-modify-private playlist-modify-public"      # Scopes must be separated by a space. 

ACCURACY_NORMAL                     = 0.80                                                  # Accuracy for comparing strings       
ACCURACY_PRECISE                    = 0.95                                                  # Accuracy for comparing strings
SEARCH_ANALYSIS_LIMIT               = 3                                                     # Number of song results to search for in every search request
MAX_NUMBER_OF_TRACKS                = 9999                                                  # Max number of tracks to search for (Spotify Limit)

search_track_IDs                    = []  # Track IDs that were found successfully
zero_found_list                     = []  # Tracks with no search result are listed here
tracks_in_playlist                  = []  # Tracks which are in playlist get listed here
tracknames_not_identical            = []  # Tracks that were added and are NOT identical to the mp3 list are listed here
mp3_list_original                   = []  # List of all mp3 files in the folder
mp3_list                            = []  # List of all mp3 files in the folder, unchanged

## DEF FUNCTIONS
def read_files_from_path(path):
    """
    Reads all file names from a given directory path.

    Args:
        path (str): The path to the directory to read file names from.

    Returns:
        list: A list of all file names in the directory.
    """
    full_name_list = [name for name in os.listdir(path)]  # read all file names from path directory
    return full_name_list

def spotify_authentication(client_id, client_secret, scope):
    """
    Function: generates spotipy object that is "logged in".

    Authentication and Authorization:

    client_id and client_secret from Spotify Developer dashboard. "User for Login"
    redirect uri always the same, general link used for authorization (same as in the Dashboard under Settings).
    scope is the permission requested.

    SCOPE overview: https://developer.spotify.com/documentation/general/guides/authorization/scopes/

    """
    sp = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id=client_id,
                                                  client_secret=client_secret,
                                                  redirect_uri="http://localhost",
                                                  scope=scope,
                                                  cache_handler=None))
    return sp

def compare_strings(string1, string2, compare_ratio=0.85):
    """
    Compare two strings and return a list containing the similarity ratio and a boolean value indicating if the ratio is greater than the compare ratio.

    Args:
    string1 (str): The first string to compare.
    string2 (str): The second string to compare.
    compare_ratio (float, optional): The minimum similarity ratio required for the boolean value to be True. Defaults to 0.5.

    Returns:
    list: A list containing the similarity ratio and a boolean value indicating if the ratio is greater than the compare ratio.

    Uses the SequenceMatcher class from the difflib module to calculate the similarity ratio between the strings.
    """

    data = [0, False]

    # Calculate the similarity ratio between the strings
    data[0] = difflib.SequenceMatcher(None, string1, string2).ratio()

    # Check if the ratio is greater than the compare ratio
    if data[0] > compare_ratio:
        data[1] = True

    return data

def remove_special_characters(string):
    """
    Remove special characters from a string.

    Args:
        string (str): The string to remove special characters from.

    Returns:
        str: The string without special characters.
    """
    special_characters = ["(", ")", "[", "]", "{", "}", ",", ".", "!", "?", ":", ";", "-", "_", "+", "=", "/", "\\", "|", "<", ">", "@", "#", "$", "%", "^", "*", "~", "`"]
    for character in special_characters:
        string = string.replace(character, "")
    return string

def move_mp3_file_into_new_folder(mp3_list_original, i):
    """
    Moves mp3 files from the original location to a new directory.

    Args:
        mp3_list_original (list): A list of mp3 file names.
        i (int): The index of the file to be moved.

    Returns:
        None
    """
    source_path = os.path.join(PATH_MUSIC, mp3_list_original[i])

    # Create new directory for not identical tracks
    new_directory = os.path.join(PATH_MUSIC, "NotIdenticalTracks")
    if not os.path.exists(new_directory):
        os.makedirs(new_directory)
            
    destination_path = os.path.join(new_directory, mp3_list_original[i])

    # Move the file
    shutil.move(source_path, destination_path)

## MAIN CODE

print("---------------------------------------------------------------------------------------\n")
print("--> Spotify Local Music Importer started!")

# Read Spotify Login data from secret json file or ask for manual user input
try:
    with open('secrets.json') as file:
        login_data = json.load(file)
        SPOTIFY_CLIENT_ID     = login_data['spotify_client_id']
        SPOTIFY_CLIENT_SECRET = login_data['spotify_client_secret']
        SPOTIFY_ACC           = login_data['user_account_name']
except FileNotFoundError:
    print("--> Secrets file not found.")
    user_input = input("Do you want to continue and manually enter your Spotify Data? (y/n): ")
    if user_input.lower() == "y":
        SPOTIFY_CLIENT_ID = input("Enter your Spotify client ID: ")
        SPOTIFY_CLIENT_SECRET = input("Enter your Spotify client secret: ")
        SPOTIFY_ACC = input("Enter your Spotify account name: ")
    else:
        raise SystemExit("Exiting the program - No Spotify data entered")
except KeyError:
    print("--> Invalid format in secrets.json file.")
    raise SystemExit("Exiting the program - Invalid format in secrets.json file")

print("--> Spotify login data read successfully.")

# Read mp3 files from path and filter to only include .mp3 files
try:
    PATH_MUSIC = input("--> Enter the path to the directory where the music files are located: ").replace('\\', '/')  # Get path to music directory from user
    #PATH_MUSIC = 'C:/Users/Master/Desktop/MusikVaterFavorites' ### Use this line for testing faster - DELETE THIS LINE FOR FINAL VERSION ###
    full_folder_list = read_files_from_path(PATH_MUSIC)
    mp3_list_original = [name for name in full_folder_list if name.endswith(".mp3")]
except FileNotFoundError:
    print("--> Error: Path not found.")
except Exception as e:
    print(f"--> Error: {str(e)}")
    raise SystemExit("Exiting the program - Error in reading the mp3 files")

mp3_list = mp3_list_original.copy()

# Remove special characters from mp3_list
for k in range(len(mp3_list)):
    mp3_list[k] = mp3_list[k].replace('.mp3', '')
    mp3_list[k] = mp3_list[k].replace(' - ', ' ')
    mp3_list[k] = mp3_list[k].lower()

print("--> mp3 list read successful.")
    
# Ask user for accuracy of comparison
user_input = input("--> Do you want to use the normal compare ratio or the precise compare ratio? \nType \"n\" for normal or \"p\" for precise: ")
if user_input == "p":
    COMPARE_RATIO_DIFFLIB = ACCURACY_PRECISE
    print(f"--> compare ratio set to Precise: {ACCURACY_PRECISE}")
else:
    COMPARE_RATIO_DIFFLIB = ACCURACY_NORMAL
    print(f"--> compare ratio set to Normal: {ACCURACY_NORMAL}")

# Ask user whether he wants to doublecheck bad comparison results manually during the search
user_input = input("--> Do you want to doublecheck bad comparison results manually during the search? \nType \"y\" or \"n\":")
if user_input == "y":
    DOUBLECHECK_SEARCH = True
    print("--> Doublecheck enabled.")
else:
    DOUBLECHECK_SEARCH = False
    print("--> Doublecheck disabled.")

# Ask user for creation of log file
user_input = input("--> Do you want to generate a log file with the results? \nType \"y\" or \"n\":")
if user_input == "y":
    GENERATE_LOG_FILE = True
    print("--> Log file will be generated.")
else:
    GENERATE_LOG_FILE = False
    print("--> Log file will not be generated.")

# Write the mp3_list to log.csv file
try:
    os.chdir(PATH_MUSIC)  # Change directory to PATH_MUSIC to avoid VS code path error
    if GENERATE_LOG_FILE:
        with open('log.csv', 'w', newline='') as file:
            writer = csv.writer(file, quoting=csv.QUOTE_ALL, delimiter=";")
            writer.writerow(["TRACK STATE", "MP3 NAME FROM LOCAL DIRECTORY", "SEARCHED SPOTIFY RESULT", "COMPARE RATIO"])  # Add the titles as the first row
except Exception as e:
    print(f"Error: {str(e)}")

try:
    spotify = spotify_authentication(SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET, SPOTIFY_SCOPE) 
except Exception as e:
    print(f"Error: {str(e)}")

print("--> Spotify authentication successful.")

# Search for tracks and compare them with the original track name
for i in range(len(mp3_list)):

    # Check if max number of tracks is reached (Spotify limits the number of tracks that can be added to a playlist at once)
    if i == MAX_NUMBER_OF_TRACKS:
        break    

    compare_ratios                      = [] 
    compare_ratios_booleans             = []
    track_name_correct                  = False
    track_artist_correct                = False
    overruled                           = False

    # Search Tracks from list with mp3 names as input with spotify api
    search_result = spotify.search(mp3_list[i], limit=SEARCH_ANALYSIS_LIMIT)

    # Check if no search results
    if search_result["tracks"]["total"] == 0:
        zero_found_list.append(mp3_list[i])
        continue

    # filter out track name and artist name from search results and compare them with the original track name
    for track in search_result["tracks"]["items"]:

        # filter out track name and artist name from search results and remove special characters
        found_trackname = (track["name"])
        found_track_artist = (track["artists"][0]["name"])

        found_trackname = found_trackname.lower()
        found_track_artist = found_track_artist.lower()

        found_trackname_full = found_track_artist + " " + found_trackname

        # Compare found and searched strings to get similarity ratio using difflib
        compare_result = compare_strings(mp3_list[i], found_trackname_full, COMPARE_RATIO_DIFFLIB)

        compare_ratios.append(compare_result[0])
        compare_ratios_booleans.append(compare_result[1])

    # Get index of highest compare ratio
    index = compare_ratios.index(max(compare_ratios))

    # If index is below chosen ration, ask user whether he still wants to add the found track
    if DOUBLECHECK_SEARCH and compare_ratios[index] < COMPARE_RATIO_DIFFLIB:
        user_input = input(f"--> The track number {i+1} was found with a similarity ratio of {round(compare_ratios[index],2)}.\n--> Search input:\t{mp3_list[i]}\n--> Found track:\t{search_result['tracks']['items'][index]['artists'][0]['name'].lower()} {search_result['tracks']['items'][index]['name'].lower()}\nDo you still want to add this track? (y/n):")
        
        if user_input == "y":
            search_track_IDs.append(search_result["tracks"]["items"][index]["id"])
            overruled = True
        else:
            tracknames_not_identical.append(mp3_list[i])
            
            # Move the file to a new directory
            move_mp3_file_into_new_folder(mp3_list_original, i)
            
    else:
        if compare_ratios_booleans[index] == True:
            search_track_IDs.append(search_result["tracks"]["items"][index]["id"])
        else:
            tracknames_not_identical.append(mp3_list[i])
            
            # Move the file to a new directory
            move_mp3_file_into_new_folder(mp3_list_original, i)


    if GENERATE_LOG_FILE:
        with open('log.csv', 'a', newline='', encoding='utf-8') as file:
            writer = csv.writer(file, quoting=csv.QUOTE_ALL, delimiter=";")
            
            # Set status for log file 
            if  mp3_list[i] in tracknames_not_identical:
                status = "Not Identical"

            if overruled:
                status = "Success (Overruled)"

            if compare_ratios_booleans[index] == True:
                status = "Success"

            writer.writerow([status, mp3_list[i], search_result["tracks"]["items"][index]["artists"][0]["name"].lower() + " " + search_result["tracks"]["items"][index]["name"].lower(), round(compare_ratios[index],2)])

    # Print progress
    if len(mp3_list) != 0:
        progress = round((i + 1) / len(mp3_list) * 100)
        print(f"--> Search progress: {progress}%", end="\r")


# Add statistics to csv file
if GENERATE_LOG_FILE:
    with open('log.csv', 'a', newline='') as file:
        writer = csv.writer(file, quoting=csv.QUOTE_ALL, delimiter=";")
        writer.writerow(["", "", "", ""])
        writer.writerow(["STATISTICS"])
        writer.writerow(["Number of tracks in mp3 folder", len(mp3_list)])
        writer.writerow(["Successfully found tracks", len(search_track_IDs)])
        writer.writerow(["Not identical tracks", len(tracknames_not_identical)])
        writer.writerow(["Amount of zero found results", len(zero_found_list)])
        writer.writerow(["Success rate Search (%)", round(len(search_track_IDs) / len(mp3_list) * 100, 2)])
        writer.writerow(["Success rate Playlist", round(len(tracks_in_playlist) / len(mp3_list) * 100, 2)])

print("--> Search and comparison successful.")

user_answer_add_tracks = input("--> Do you want to add the tracks to a Spotify playlist? \nType \"y\" or \"n\":")

# Add searched IDs
if user_answer_add_tracks == "y":

    # Create new Playlist
    if input("--> Do you want to create a new playlist? \nType \"y\" or \"n\":") == "y":
        name = input("--> Enter new Playlist name:")
        user = spotify.current_user()
        user_id = user['id']
        response = spotify.user_playlist_create(user_id, name, False)
        playlist_id = response["id"]
    else:
        playlist_id = input("Enter existing playlist ID:")

    print("--> Wait until tracks are added to playlist...")

    # Add tracks to playlist
    for i in range(0, len(search_track_IDs), 99): # Spotify limit is 100 tracks per request
        spotify.playlist_add_items(playlist_id, search_track_IDs[i:i+100])
        
    print("--> Tracks added to playlist successfully.")

    # Get Data from Playlist
    print("--> Getting data from playlist...")
    rawdata1 = spotify.playlist(playlist_id)  # Get data of playlist
    number_of_tracks = rawdata1["tracks"]["total"]  # Get number of tracks from playlist data

    # Get track names from new playlist
    for i in range(number_of_tracks):
        rawdata2 = spotify.playlist_tracks(playlist_id, fields="items(track(name,album(!available_markets),artists(name)))", limit=1, offset=i)
        track_name = rawdata2["items"][0]["track"]["name"]
        track_artist = rawdata2["items"][0]["track"]["artists"][0]["name"]
        full_track_name = track_artist + " - " + track_name
        tracks_in_playlist.append(full_track_name)   

    # Write tracks on playlist to log.csv file
    if GENERATE_LOG_FILE:
        with open('log.csv', 'a', newline='') as file:
            writer = csv.writer(file, quoting=csv.QUOTE_ALL, delimiter=";")
            writer.writerow(["", "", "", ""])
            writer.writerow(["TRACKS IN NEW PLAYLIST"])
            for track in tracks_in_playlist:
                writer.writerow([track])
else:
    print("--> No tracks were added to a playlist.")

# Print statistics
if len(zero_found_list) != 0:
    print(f"\n--> List of no search results\t\t\t({len(zero_found_list)}):\n{zero_found_list}\n")
if len(tracks_in_playlist) != 0:
    print(f"--> Number of tracks in created playlist: {len(tracks_in_playlist)}")
if len(mp3_list) != 0:
    print(f"--> Number of tracks in mp3 folder: {len(mp3_list)}")
if len(tracknames_not_identical) != 0:
    print(f"--> List of tracks that were not added successfully from the folder: {len(tracknames_not_identical)}")

print(f"--> Success rate Spotify search: {round(len(search_track_IDs)/len(mp3_list)*100,2)}%")

print("\n--> Spotify Local Music Importer has finished!\n")
print("---------------------------------------------------------------------------------------\n")
