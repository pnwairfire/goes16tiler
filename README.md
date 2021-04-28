# goes16tiler
A python utility to create a basemap of GOES-16 imagery for CONUS or North America

## Requirements
**From your system**
- Python >= 3.8
- GDAL >= 3.2
- NetCDF Driver for GDAL

**From Dockerfile**
- docker-compose v.3
- docker 

*note: if using docker you should allocate plenty of CPU + Memory to your containers to handle the GDAL+NetCDF transformations* 


## Overview
The functionality is contained in the class `GOES16Tiler`. It has not been completely packaged, so from the directory you would import: 

```
from goes16tiler import GOES16Tiler

# load the module
g = GOES16Tiler()
```

The module can be instansiated stand-alone, but it takes several arguements:
### Arguments
- **timezone:** defaults to UTC, but can be changed to your systems timezone
- **location_info:** Information used by the [astral](https://astral.readthedocs.io/en/latest/index.html) package to determine 
whether or not to pull daytime or nightime channels. For example, true color band combinations won't show at night. Why not use Cloud Top Phase or LWIR? 
The default city used for CONUS is Seattle, as it's far enough west to capture the U.S.
```
DEFAULT_CITY = {
    "city": 'Seattle',
    "country": 'United States',
    "olson_tz": 'US/Pacific',
    "lat": 47.65,
    "lng": -122.28
}
```
- **day_channels:** Default band combinations for when it's "daytime". These are static as I have not tried implementing too many or using ones that require calculations between bands. 
could be done without too much effort. Defaults to `TRUE_COLOR = "C01 C02 C03"`.
- **night_channels:** Default band combinations for when it's "night". Defaults to `LWIR = "C16"`
- **zoom**: Controls the level at which gdal2tiles.py will tile the produced tif. The deeper the zoom, the more intensive the process. It's also diminishing returns as
GOES16 isn't high resolution. Default is 8, but I found 9 can be helpful if you have the processing power and time. 
- **cutline:** Defaults to 'conus', which is geojson of the continenal United States stored in `spatial_data/`. Also a cutline arguement for north america that can be used called `full`.
Additionally you may pass in any valid geojson file you like to cut. Make sure it's using EPSG::3857 and has CRS set as: `"crs": { "type": "name", "properties": { "name": "urn:ogc:def:crs:EPSG::3857" } }`. 




