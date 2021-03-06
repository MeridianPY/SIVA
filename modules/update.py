from requests import get
import zipfile
from tkinter import messagebox

def update(interface):
    data = get(interface.data["version_url"])
    with open("./{0}/siva_update.zip".format(interface.data["directory_name"]), "wb") as out:
        out.write(data.content)
    zip = zipfile.ZipFile("./siva_files/siva_update.zip", "r")
    zip.extractall("./")
    zip.close()
    messagebox.showinfo("Updater", "Download complete. Please delete the old version and use the new one.")
