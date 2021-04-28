import boto3
import botocore
from botocore import UNSIGNED
from botocore.config import Config

__author__ = "Stuart Illson"

# Single GOES-16 Product for now
GOES_PRODUCT = "L1b-RadC"

class s3Utils(object):

  def __init__(self):
        self.s3 = boto3.resource('s3', config=Config(signature_version=UNSIGNED))
        self.noaa_bucket = self.s3.Bucket('noaa-goes16')

  def nc_files_at_hour(self, dt):
    # Make sure to pass in a datetime that has been localized
    year = dt.strftime("%Y")
    day = dt.strftime("%j")
    hour = dt.strftime("%H")
    s3_path = f"ABI-{GOES_PRODUCT}/{year}/{day}/{hour}"
    objs = self.noaa_bucket.objects.filter(Prefix=s3_path)
    # build and return a list
    list_objs = []
    for i in objs:
      list_objs.append(i.key)

    return(list_objs)

  def download_nc_file(self, path, local_name):
    self.noaa_bucket.download_file(path, local_name)