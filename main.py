import numpy as np  # numpy module
import netCDF4 as nc  # netcdf module
from flask import jsonify


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


def heatwave_api(request):
    # Get lat and lon from request body
    request_json = request.get_json()
    print(request_json)

    if request_json and "lat" in request_json:
        input_lat = request_json["lat"]
    else:
        input_lat = -27.4698
    if request_json and "lon" in request_json:
        input_lon = request_json["lon"]
    else:
        input_lon = 153.0251

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

    return jsonify(return_value)


if __name__ == "__main__":
    from flask import Flask, request
    app = Flask(__name__)

    @app.route('/', methods=["GET", "POST"])
    def index():
        return heatwave_api(request)

    app.run('127.0.0.1', 8000, debug=True)
