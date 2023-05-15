# WGS72 value; taken from https://geographiclib.sourceforge.io/html/NET/NETGeographicLib_8h_source.html
EARTH_RADIUS= 6378135.0
MU_EARTH= 3.98574405e+14
SECONDS_SIDEREAL_DAY= 86164
RADIO_K_FACTOR: 1
# The K-factor varies according to temperature, humidity..
# As I don't care for now about it, I set it to 1 although the standard value is 1,33.
# If you change it, dont forget to take it into account in the ns-3 C++ code
