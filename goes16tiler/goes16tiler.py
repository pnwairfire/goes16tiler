###############################################
#  GOES 16 Tileset Generator
###############################################

###############################################
# LICENSE
# Copyright (C) 2021 Stuart Illson University of Washington Pacific Wildland Fire Sciences Laboratory
#
# This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.
# This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
# You should have received a copy of the GNU General Public License along with this program. If not, see http://www.gnu.org/licenses/.
###############################################

###############################################
# This program was inspired by the work at the University of Kentucky and University of Costa Rica (UCR)
# Special thanks to Boyd Shearer for writing and sharing excellent code end-to-end.
###############################################
__author__ = "Stuart Illson"

from datetime import datetime
from astral import LocationInfo
from astral.sun import sun
import subprocess
import json
import pytz

from .s3utils import s3Utils

# Band Combinations set in R-G-B order if multi-band
NATURAL_FIRE =  "C06 C03 C02"
LWIR = "C16"
TRUE_COLOR = "C02 C03 C01"
CLOUD_TOP: "C11"

DEFAULT_CITY = {
    "city": 'Seattle',
    "country": 'United States',
    "olson_tz": 'US/Pacific',
    "lat": 47.65,
    "lng": -122.28
}

GOES_PRODUCT = "L1b-RadC"
PROJ = "'+proj=geos +lon_0=-75 +h=35786023 +x_0=0 +y_0=0 +ellps=GRS80 +units=m +no_defs  +sweep=x'"

class GOES16Tiler(object):
    """
        The GOES16 Tile Generator class is a utility to step through
        building a tileset off of publicly available GOES-16 imagery
        provided by NOAA.

        Configuration is currently limited, however the class is constructed
        such that it shouldn't be too hard to implement switches to
        accommodate dynamically changing mode (day/night) for user-defined
        locations, adding more bands/combos such as TRUE_COLOR. Calculated
        products such as NIGHTIME_MICROPHYSICS will take more development.
    """

    def __init__(self, timezone="UTC", location_info=DEFAULT_CITY, day_channels=TRUE_COLOR,
                 night_channels=LWIR, zoom=8, cutline='conus'):
        self.dt = self.get_datetime()
        self.naive_dt = datetime.utcnow()
        self.astral_location = self.get_astral_location(location_info)
        self.mode, self.channels = self.day_or_night(day_channels, night_channels)
        self.zoom = zoom
        self.nc_files_to_pull = []
        self.s3_utils = s3Utils()
        self.cutline = self.cutline_geojson(cutline)
        self.print_config()


    def get_datetime(self):
        # Current time UTC
        dt = datetime.utcnow()
        dt = pytz.timezone('UTC').localize(dt)
        print(dt)
        return(dt)

    def get_astral_location(self, location_info):
        """
        Get city information using the astral package. For a list
        of complete timezones, see: https://en.wikipedia.org/wiki/List_of_tz_database_time_zones
        """
        city = LocationInfo(location_info["city"],
                            location_info["country"],
                            location_info["olson_tz"],
                            location_info["lat"],
                            location_info["lng"])
        return(city)

    def day_or_night(self, day_channels, night_channels):
        s = sun(self.astral_location.observer, date=self.dt)
        # Select bands based if the sun has set
        if (self.dt > s["sunrise"]) and (self.dt < s["sunset"]):
            channels = day_channels
            mode = "day"
        elif (self.dt < s["sunrise"]):
            channels = night_channels
            mode = "night"
        elif (self.dt > s["sunset"]):
            channels = night_channels
            mode = "night"
        else:
            channels = night_channels
            mode = "night"
        return mode, channels

    def cutline_geojson(self, cutline):
        # I'm providing two cutline defaults
        # but allowing input for any valid geojson file
        if cutline == 'conus':
            path = "./spatial_data/conus.geojson"
        elif cutline == 'full':
            path = "./spatial_data/full.geojson"
        else:
            path = cutline
        return(path)


    def print_config(self):
        print("### GOES16Tiler Parameters ###\n")
        print(f"Selecting channels for time of day:{self.mode}\n"
              f"TIME: {self.dt}\n"
              f"CHANNELS {self.channels}")
        print(f"PRODUCTS: {GOES_PRODUCT}")
        print(f"PROJECTION INFO: {PROJ}")
        print(f"TILING LEVEL: {self.zoom}\n")
        print((
            f"Location is set at {self.astral_location.name}/{self.astral_location.region}\n"
            f"with timezone: {self.astral_location.timezone}\n"
            f"and Latitude: {self.astral_location.latitude:.02f}; Longitude: {self.astral_location.longitude:.02f}\n"
        ))

    def clean_previous_run(self):
        # Clean before running
        shell_delete_cmd = f"""
            echo "Removing past run..."
            rm -v ./temp/*.tif
            rm -v ./temp/*.xml
        """
        process_delete = subprocess.run(shell_delete_cmd, shell=True, stdout=subprocess.PIPE)
        print("Deleting previous run...")
        print(process_delete.stdout.decode('UTF-8'))

    def search_for_files(self):
        # GOES-16 File Parameters
        dt = pytz.utc.localize(self.naive_dt, is_dst=None).astimezone(pytz.timezone(self.astral_location.timezone))

        all_files = self.s3_utils.nc_files_at_hour(dt)

        channels = self.channels.split(' ')

        self.nc_files_to_pull = []
        for channel in channels:
            result = list(filter(lambda x: channel in x, all_files))
            item = {"channel": channel, "path": result[-1]}
            self.nc_files_to_pull.append(item)

        print("netCDF files to download:\n")
        for obj in self.nc_files_to_pull:
            print(obj["path"])

    def download_nc_files(self):
        print("### DOWNLOADING NETCDF FILES ###\n")
        if len(self.nc_files_to_pull) > 0:
            for obj in self.nc_files_to_pull:
                path = obj["path"]
                local_fn = "./temp/" + obj["channel"] + ".nc"
                print(f"S3 FILE: {path}\n"
                      f"LOCAL FILE: {local_fn}\n")
                self.s3_utils.download_nc_file(path, local_fn)

    def format_nc_to_tiff(self):
        # Convert NC File to a GeoTIFF
        for i in self.channels.split():
            print(f"Translating {i} to GTiff format... ")
            translate_cmd = f"""
                gdal_translate NETCDF:./temp/{i}.nc:Rad ./temp/{i}.tif
                rm ./temp/{i}.nc
                gdalinfo -stats ./temp/{i}.tif
            """
            completed = subprocess.run(translate_cmd, shell=True, stdout=subprocess.PIPE)
            print(completed.stdout.decode('UTF-8'))

        # Reproject the Images and tone them to 255
        for i in self.channels.split():
            bandinfo = subprocess.run(f"gdalinfo -stats -json ./temp/{i}.tif", shell=True, stdout=subprocess.PIPE)
            bandmeta = json.loads(bandinfo.stdout.decode('UTF-8'))

            hi = bandmeta['bands'][0]['mean'] + (bandmeta['bands'][0]['stdDev']*3)
            lo = bandmeta['bands'][0]['min'] #+ (bandmeta['bands'][0]['stdDev']*0.5)
            print(f"************* For {i} applying minimum: {lo} and maximum: {hi} -- no worries about GDAL errors! *************")
            scale_day_cmd = f"""
            gdal_translate -ot Byte -of Gtiff -scale {lo} {hi} 0 255 ./temp/{i}.tif './temp/_scale_'{i}.tif
            gdalwarp './temp/_scale_'{i}.tif -t_srs EPSG:3857 -s_srs {PROJ} -r cubic -of Gtiff  './temp/_prj_'{i}.tif
            gdalwarp -cutline {self.cutline} -crop_to_cutline './temp/_prj_'{i}.tif './temp/_us_'{i}.tif
            rm './temp/_scale_'{i}.tif; rm './temp/_prj_'{i}.tif rm {i}.tif;
            """
            scale_night_cmd = f"""
            gdal_translate -ot Byte -of Gtiff -scale {lo} {hi} 255 0 ./temp/{i}.tif './temp/_scale_'{i}.tif
            gdalwarp './temp/_scale_'{i}.tif -t_srs EPSG:3857 -s_srs {PROJ} -r cubic -of Gtiff  './temp/_prj_'{i}.tif
            gdalwarp -cutline {self.cutline} -crop_to_cutline './temp/_prj_'{i}.tif './temp/_us_'{i}.tif
            rm './temp/_scale_'{i}.tif; rm './temp/_prj_'{i}.tif rm {i}.tif;
            """
            if self.mode == "day":
                scale = subprocess.run(scale_day_cmd, shell=True, stdout=subprocess.PIPE)
            else:
                scale = subprocess.run(scale_night_cmd, shell=True, stdout=subprocess.PIPE)

            print(scale.stdout.decode('UTF-8'))

    def merge_tiffs(self):
        bands = self.channels.split()
        if len(bands) > 1:
            print(f"************* Processing bands into RGB *************")
            merge_cmd = f"""
            gdal_merge.py -separate  -a_nodata 255 255 255 -o ./temp/rgb.tif -co PHOTOMETRIC=RGB './temp/_us_'{bands[0]}.tif './temp/_us_'{bands[1]}.tif './temp/_us_'{bands[2]}.tif
            """
            merge = subprocess.run(merge_cmd, shell=True, stdout=subprocess.PIPE)
            print(merge.stdout.decode('UTF-8'))
        else:
            print(f"************* No merging for single band *************")

    def tile_tiffs(self):
        if self.mode == "day":
            print(f"************* Tiling the Day set *************")
            tile_cmd = f"""
            gdal2tiles.py -x -p mercator -z '0-'{self.zoom} -w all -r average -a 0.0 ./temp/rgb.tif tiles
            """
            tile = subprocess.run(tile_cmd, shell=True, stdout=subprocess.PIPE)
        else:
            print(f"************* Tiling the Night Set *************")
            tile_cmd = f"""
            gdal2tiles.py -p mercator -z '0-'{self.zoom} -w all -r average -a 0.0 './temp/_us_'{self.channels}.tif tiles
            """
            tile = subprocess.run(tile_cmd, shell=True, stdout=subprocess.PIPE)

        print(tile.stdout.decode('UTF-8'))

    def build_tileset(self):
        self.clean_previous_run()
        self.search_for_files()
        self.download_nc_files()
        self.format_nc_to_tiff()
        self.merge_tiffs()
        self.tile_tiffs()

        # IMPLEMENT S3 SYNC functionality later?
        # def push_tiles_to_s3(self):
        #     print(f"************* Pushing Tiles to S3 *************")
        #     push_tiles_cmd = f"""
        #     echo "Pushing Tiles to S3 production tiles."
        #     aws s3 sync tiles/ 's3://'{self.s3_bucket} --acl public-read
        #     rm -r tiles/*
        #     """

        #     push_tiles = subprocess.run(push_tiles_cmd, shell=True, stdout=subprocess.PIPE)
        #     print(push_tiles.stdout.decode('UTF-8'))

