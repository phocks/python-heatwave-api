import numpy as np  # numpy module
import netCDF4 as nc  # netcdf module
from flask import jsonify


def heatwave_api(request):
    request_json = request.get_json()
    print(request_json)

    in_nc = nc.Dataset("./data/CCRC_NARCliM_YEA_1950-2009_HWN_EHF_NF13.nc")
    print(in_nc)

    temps = in_nc.variables['HWN_EHF']
    mt = in_nc.variables['time']  # read time variable

    time = mt[:]  # Reads the netCDF variable MT, array of one element
    print(time)
    time_unit = in_nc.variables["time"].getncattr('units')
    time_cal = in_nc.variables["time"].getncattr(
        'calendar')  # read calendar type
    local_time = nc.num2date(time, units=time_unit,
                             calendar=time_cal)  # convert time
    print("Original time %s is now converted as %s" %
          (time[0], local_time[0]))  # check conversion

    lat, lon = in_nc.variables['lat'], in_nc.variables['lon']

    target_lat = -27.4698
    target_lon = 153.0251

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
    print(iy_min, ix_min)

    temps_vals = temps[:]
    temperature_dict = {}

    for year in range(19):
        print(temps[year, iy_min, ix_min])
        temperature_dict[str(local_time[year].year)] = int(
            temps[year, iy_min, ix_min])

    return jsonify(temperature_dict)


if __name__ == "__main__":
    from flask import Flask, request
    app = Flask(__name__)

    @app.route('/', methods=["GET", "POST"])
    def index():
        return heatwave_api(request)

    app.run('127.0.0.1', 8000, debug=True)
