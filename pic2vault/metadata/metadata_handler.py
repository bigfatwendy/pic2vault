import piexif
from PIL import Image
from geopy.geocoders import Nominatim
from datetime import datetime

def deg_to_dms_rational(deg_float):
    """Convert decimal degrees to degrees/minutes/seconds tuple"""
    deg = int(deg_float)
    min_float = (deg_float - deg) * 60
    minute = int(min_float)
    sec_float = (min_float - minute) * 60
    return [
        (deg, 1),
        (minute, 1),
        (int(sec_float * 100), 100)
    ]

def set_exif_data(image_path, date_str=None, location_name=None):
    exif_dict = {"0th": {}, "Exif": {}, "GPS": {}}
    try:
        exif_dict = piexif.load(image_path)
    except:
        pass  # No EXIF? We start fresh

    # Set DateTimeOriginal
    if date_str:
        try:
            formatted = datetime.strptime(date_str, "%Y-%m-%d").strftime("%Y:%m:%d %H:%M:%S")
            exif_dict["Exif"][piexif.ExifIFD.DateTimeOriginal] = formatted.encode()
        except Exception as e:
            print(f"Invalid date: {e}")

    # Set GPS data from location name
    if location_name:
        try:
            geolocator = Nominatim(user_agent="pic2vault")
            location = geolocator.geocode(location_name)
            if location:
                lat_dms = deg_to_dms_rational(abs(location.latitude))
                lon_dms = deg_to_dms_rational(abs(location.longitude))
                exif_dict["GPS"][piexif.GPSIFD.GPSLatitude] = lat_dms
                exif_dict["GPS"][piexif.GPSIFD.GPSLatitudeRef] = b'N' if location.latitude >= 0 else b'S'
                exif_dict["GPS"][piexif.GPSIFD.GPSLongitude] = lon_dms
                exif_dict["GPS"][piexif.GPSIFD.GPSLongitudeRef] = b'E' if location.longitude >= 0 else b'W'
            else:
                print("Location not found.")
        except Exception as e:
            print(f"Geolocation error: {e}")

    # Save new EXIF data to image
    exif_bytes = piexif.dump(exif_dict)
    image = Image.open(image_path)
    image.save(image_path, exif=exif_bytes)

def read_exif_data(image_path):
    try:
        exif_dict = piexif.load(image_path)
        date = exif_dict["Exif"].get(piexif.ExifIFD.DateTimeOriginal, b"").decode()
        gps = exif_dict.get("GPS", {})
        return {
            "date": date,
            "gps": gps
        }
    except Exception as e:
        print(f"Failed to read EXIF: {e}")
        return {}
