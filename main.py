import numpy as np  # numpy module
import netCDF4 as nc  # netcdf module
from flask import jsonify
import math

# AUS_CENTER = {"lat": -25.2744, "lon": 133.7751}
# NUDGE_FACTOR = 0.01

# Check if all values are zero


def is_all_zero(dict):
    for key in dict.keys():
        if dict[key] > 0:
            return False
    return True


def get_temperature_dict(file, input_lat, input_lon):
    in_nc = nc.Dataset(file)

    temps = in_nc.variables['HWD_EHF']
    mt = in_nc.variables['time']  # read time variable

    time = mt[:]  # Reads the netCDF variable MT, array of one element

    time_unit = in_nc.variables["time"].getncattr('units')
    time_cal = in_nc.variables["time"].getncattr(
        'calendar')  # read calendar type
    local_time = nc.num2date(time, units=time_unit,
                             calendar=time_cal)  # convert time
    # print("Original time %s is now converted as %s" %
    #       (time[0], local_time[0]))  # check conversion

    lat, lon = in_nc.variables['lat'], in_nc.variables['lon']

    target_lat = input_lat
    target_lon = input_lon

    latvals = lat[:]
    lonvals = lon[:]  # extract lat/lon values (in degrees) to numpy arrays

    # Convert lat lon to position in 2D array
    def getclosest_ij(lats, lons, latpt, lonpt):
        # find squared distance of every point on grid
        dist_sq = (lats-latpt)**2 + (lons-lonpt)**2
        minindex_flattened = dist_sq.argmin()  # 1D index of minimum dist_sq element
        # Get 2D index for latvals and lonvals arrays from 1D index
        return np.unravel_index(minindex_flattened, latvals.shape)

    iy_min, ix_min = getclosest_ij(latvals, lonvals, target_lat, target_lon)
    #print(iy_min, ix_min)

    temps_vals = temps[:]
    temperature_dict = {}

    for year in range(len(local_time)):
        #print(temps[year, iy_min, ix_min])
        temperature_dict[str(local_time[year].year)] = int(
            temps[year, iy_min, ix_min])

    return temperature_dict


def main_process(input_lat, input_lon):
    print(input_lat, input_lon)

    historical = get_temperature_dict(
        "./data/CCRC_NARCliM_YEA_1950-2009_HWD_EHF_NF13.nc", input_lat, input_lon)
    modern = get_temperature_dict(
        "./data/CCRC_NARCliM_YEA_1990-2009_HWD_EHF_NF13.nc", input_lat, input_lon)
    projection_1 = get_temperature_dict(
        "./data/CCRC_NARCliM_YEA_2020-2039_HWD_EHF_NF13.nc", input_lat, input_lon)
    projection_2 = get_temperature_dict(
        "./data/CCRC_NARCliM_YEA_2060-2079_HWD_EHF_NF13.nc", input_lat, input_lon)

    return_value = {
        "historical": historical,
        "modern": modern,
        "projection_1": projection_1,
        "projection_2": projection_2
    }

    return return_value


def heatwave_api(request):
    # Get lat and lon from request body
    request_json = request.get_json()
    # print(request_json)

    if request_json and "lat" in request_json:
        input_lat = request_json["lat"]
    else:
        input_lat = -27.4698
    if request_json and "lon" in request_json:
        input_lon = request_json["lon"]
    else:
        input_lon = 153.0251

    # In case we get a GET request lat lon
    input_get_lat = request.args.get("lat")
    input_get_lon = request.args.get("lon")

    if input_get_lat != None:
        input_lat = float(input_get_lat)
    if input_get_lon != None:
        input_lon = float(input_get_lon)

    keep_trying = True
    scan_radius = 0.1

    scan_lat = input_lat
    scan_lon = input_lon
    scan_radius = 0.5
    scan_radius_nudge = 0.5
    scan_angle = 0.0
    scan_angle_nudge = 0.25

    while keep_trying:
        final_return = main_process(scan_lat, scan_lon)

        # Check if still in the ocean
        if (is_all_zero(final_return["historical"]) and
            is_all_zero(final_return["modern"]) and
            is_all_zero(final_return["projection_1"]) and
                is_all_zero(final_return["projection_2"])):

            #     print("Likely not on land... moving position towards middle Australia")
            #     if input_lat <= AUS_CENTER["lat"]:
            #         input_lat = input_lat + NUDGE_FACTOR
            #     elif input_lat >= AUS_CENTER["lat"]:
            #         input_lat = input_lat = NUDGE_FACTOR
            #     if input_lon <= AUS_CENTER["lon"]:
            #         input_lon = input_lon + NUDGE_FACTOR
            #     elif input_lon >= AUS_CENTER["lon"]:
            #         input_lon = input_lon - NUDGE_FACTOR
            # else:
            #     keep_trying = False

            print("Likely not on land... scanning surrounding positions")
            scan_lat = input_lat + scan_radius * math.cos(scan_angle * math.pi)
            scan_lon = input_lon + scan_radius * math.sin(scan_angle * math.pi)

            scan_angle += scan_angle_nudge

            if scan_angle >= 2.0:
                scan_angle = 0.0
                scan_radius += scan_radius_nudge
        else:
            keep_trying = False

    return jsonify(final_return)


if __name__ == "__main__":
    from flask import Flask, request
    app = Flask(__name__)

    @app.route('/', methods=["GET", "POST"])
    def index():
        return heatwave_api(request)

    app.run('127.0.0.1', 8000, debug=True)
