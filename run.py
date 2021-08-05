from goes16tiler import GOES16Tiler
import subprocess

g = GOES16Tiler(day_channels="C06 C03 C02")
g.build_tileset()

# convert rgb.tif -gravity East -chop 5700X0 chop_east.png && convert chop_east.png -gravity West -chop 800X0 chop_west.png && convert chop_west.png -gravity North -chop 0X800 usa.png