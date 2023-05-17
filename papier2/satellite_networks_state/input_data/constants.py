# WGS72 value; taken from https://geographiclib.sourceforge.io/html/NET/NETGeographicLib_8h_source.html
EARTH_RADIUS= 6378135.0
MU_EARTH= 3.98574405e+14
SECONDS_SIDEREAL_DAY= 86164

RADIO_K_FACTOR= 1
# The K-factor varies according to temperature, humidity..
# It was written here so that it can be easily noticed.
# If you have any better definitive value, you may need to change it in the ns-3 C++ code