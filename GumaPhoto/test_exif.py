import urllib.request
import subprocess

urllib.request.urlretrieve("https://raw.githubusercontent.com/ianare/exif-samples/master/jpg/gps/DSCN0010.jpg", "sample.jpg")
res = subprocess.run(["exiftool", "-j", "-c", "%+.6f", "-GPSLatitude", "-GPSLongitude", "sample.jpg"], capture_output=True, text=True)
print(res.stdout)
