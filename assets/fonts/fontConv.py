import os
from PIL import BdfFontFile, PcfFontFile

directory = "./BDF/"
for entry in os.scandir(directory):
    if entry.path.endswith(".bdf") and entry.is_file():
        with open(entry.path,'rb') as fp:
            p = BdfFontFile.BdfFontFile(fp) #PcfFontFile if you're reading PCF files
            # won't overwrite, creates new .pil and .pdm files in same dir
            p.save("./PIL/" + entry.name)