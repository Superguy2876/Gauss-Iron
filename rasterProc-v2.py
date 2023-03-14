import arcpy
import math
import sys
import os
import numpy as np
from typing import Tuple
import concurrent.futures
import numba

# set arcpy projection to wkid 32647
arcpy.env.outputCoordinateSystem = arcpy.SpatialReference(32647)

# get folder of script
current_folder = os.path.dirname(os.path.abspath(__file__))
arcpy.env.workspace = current_folder + "/MyProject/MyProject.gdb"
arcpy.env.overwriteOutput = True

#using arcpy convert wkid:4326 point to wkid:32647 point
def latlon_to_xy(lon: float, lat: float) -> Tuple[float, float]:
    inputSRS = arcpy.SpatialReference(4326)
    outputSRS = arcpy.SpatialReference(32647)
    point = arcpy.Point()
    point.X = lon
    point.Y = lat
    point_geo = arcpy.PointGeometry(point, inputSRS)
    point_geo_out = point_geo.projectAs(outputSRS)
    point_out = point_geo_out.lastPoint
    return point_out.X, point_out.Y

def create_raster(array: np.ndarray, cell_size: float, corner_x: float, corner_y: float, name: str) -> None:
    cornerPoint = arcpy.Point(corner_x, corner_y)
    array = np.flip(array, 0)

    try:
      outRaster = arcpy.NumPyArrayToRaster(array, lower_left_corner=cornerPoint, x_cell_size=cell_size)
      outRaster.save('C:/Users/patto/Documents/dev/TheProjectItself/MyProject/rasterdata/' + name + '.tif')
    except RuntimeError as e:
      # split the numpy array into quaters and try again
      print('splitting array')
      array1 = array[:int(array.shape[0]/2), :int(array.shape[1]/2)]
      array2 = array[:int(array.shape[0]/2), int(array.shape[1]/2):]
      array3 = array[int(array.shape[0]/2):, :int(array.shape[1]/2)]
      array4 = array[int(array.shape[0]/2):, int(array.shape[1]/2):]
      create_raster(array1, cell_size, corner_x, corner_y, name + '_1')
      create_raster(array2, cell_size, corner_x + array1.shape[1] * cell_size, corner_y, name + '_2')
      create_raster(array3, cell_size, corner_x, corner_y + array1.shape[0] * cell_size, name + '_3')
      create_raster(array4, cell_size, corner_x + array1.shape[1] * cell_size, corner_y + array1.shape[0] * cell_size, name + '_4')

@numba.jit(nopython=True)
def puffFunc(Mass, radius):
  Dy_Coeff, Dz_Coeff = CoeffFunc(radius)

  return (Mass / (math.pi * np.sqrt(Dy_Coeff * Dz_Coeff))) * \
    np.exp(-((20 * radius)/(8 * Dy_Coeff))) * \
    np.exp(-((20 * (1.5 ** 2))/(8 * radius * Dz_Coeff)))

@numba.jit(nopython=True)
def getDistance(point1: Tuple[float, float], point2: Tuple[float, float], cell_size: float) -> float:
  dx = (point1[0] - point2[0]) * cell_size
  dy = (point1[1] - point2[1]) * cell_size
  return math.sqrt(dx ** 2 + dy ** 2)

@numba.jit(nopython=True)
def CoeffFunc(radius):
  σ_z = 0.20 * radius
  σ_y = 0.22 * radius * ((1 + 0.0004 * radius) ** - 0.5)

  Dz_Coeff = 20 *  (σ_z ** 2) / 2 / radius
  Dy_Coeff = 20 *  (σ_y ** 2) / 2 / radius

  return Dz_Coeff, Dy_Coeff

# get the neighbors of a cell if they exist
def getNeighbors(cell: Tuple[int, int], array: np.ndarray) -> list:
  neighbors = []
  for i in range(cell[0] - 1, cell[0] + 2):
    for j in range(cell[1] - 1, cell[1] + 2):
      if i >= 0 and i < array.shape[0] and j >= 0 and j < array.shape[1]:
        neighbors.append((i, j))
  return neighbors

@numba.jit(nopython=True, parallel=True)
def gaussianfunc(array: np.ndarray, x: int, y: int, value: float, cell_size: int) -> np.ndarray:
  
  addMass = 0
  # for iy, ix in np.ndindex(array.shape):
  for iy in numba.prange(array.shape[0]):
    for ix in numba.prange(array.shape[1]):
      distance = getDistance((x, y), (ix, iy), cell_size)
      try:
        addMass = puffFunc(value, distance)
      except Exception:
        addMass = 0
      
      array[iy, ix] += addMass

  return array
    

def gaussianProcessor(array: np.ndarray, sorties: list, name: str, raster_info: dict):
  
  count = 0

  for sortie in sorties:
    x = (round(sortie['x']/raster_info['cellsize']) * raster_info['cellsize'] - raster_info['x']) / raster_info['cellsize']
    y = (round(sortie['y']/raster_info['cellsize']) * raster_info['cellsize'] - raster_info['y']) / raster_info['cellsize']
    value = sortie['FeWashable']
    array = gaussianfunc(array, x, y, value, raster_info['cellsize'])
    count += 1
    print('sorties complete: ' + str(count))
  # save the array as a raster
  create_raster(array, cell_size=raster_info['cellsize'], corner_x=raster_info['x'], corner_y=raster_info['y'], name=name)


    
# given a numpy array, a point, a radius and a value, divide the value evenly among the points within the radius
def radial_divide(array: np.ndarray, point: Tuple[int, int], radius: float, value: float) -> np.ndarray:
  
  x = np.arange(array.shape[1])
  y = np.arange(array.shape[0])

  cx = point[0]
  cy = point[1]

  mask = (x[np.newaxis,:]-cx)**2 + (y[:,np.newaxis]-cy)**2 <= radius**2

  # number of points within the radius
  num_points = np.sum(mask)

  array[mask] += (value / num_points)

  return array

def staticProcessor(array: np.ndarray, sorties: list, name: str, static_type: str, raster_info: dict):
  count = 0
  for sortie in sorties:
    # get the coordinates of the point
    x = (round(sortie['x']/raster_info['cellsize']) * raster_info['cellsize'] - raster_info['x']) / raster_info['cellsize']
    y = (round(sortie['y']/raster_info['cellsize']) * raster_info['cellsize'] - raster_info['y']) / raster_info['cellsize']
    # get the value of the point
    value = sortie[static_type]
    # calculate the radius of the point
    radius = ((sortie['explosiveWeightKg'] ** -0.25) * 19.5) / raster_info['cellsize'] 
    # divide the value evenly among the points within the radius
    array = radial_divide(array, (int(x), int(y)), radius=radius, value=value)
    count += 1
    if count % 100 == 0:
      print(count)
  # save the array as a raster
  create_raster(array, cell_size=raster_info['cellsize'], corner_x=raster_info['x'], corner_y=raster_info['y'], name=name)
  return array

def main():
  current_folder = os.path.dirname(os.path.abspath(__file__))
  arcpy.env.workspace = current_folder + "/MyProject/MyProject.gdb"
  arcpy.env.overwriteOutput = True

  xmin = 102.750
  ymin = 19.450

  cell_size = 3

  # convert xmin, ymin to x, y
  xmin_metric, ymin_metric = latlon_to_xy(xmin, ymin)

  # round to nearest cell_size
  xmin_metric = round((xmin_metric / cell_size)) * cell_size
  ymin_metric = round((ymin_metric / cell_size)) * cell_size 

  xmax_metric = xmin_metric + 40000
  ymax_metric = ymin_metric + 20000

  

  dataset = 'namsouydataset'
  dateCursor = arcpy.da.SearchCursor(dataset, ['MSNDate'])
  yearStart = dateCursor.next()[0]
  yearEnd = yearStart

  for date in dateCursor:
    if date[0] < yearStart:
      yearStart = date[0]
    if date[0] > yearEnd:
      yearEnd = date[0]

  number_of_years = math.ceil((yearEnd - yearStart)/10000)
  
  sortieCursor = arcpy.da.SearchCursor(dataset, ['KMLLonDegDecimal','KMLLatDegDecimal', 'NumWeaponsDelivered', 'MSNDate', 'WeaponTypeWeight' ])

  

  sortieYearLists = []
  for i in range(number_of_years):
    sortieYearLists.append([])

# 'FeSuspende', 'FeBedded', 'FeWashable', 'ExplosionR',

  for sortie in sortieCursor:
    year = math.floor((sortie[3] - yearStart)/10000)

    sortie_dict = {}
    # convert lon, lat to x, y
    x, y = latlon_to_xy(sortie[0], sortie[1])
    sortie_dict['x'] = x
    sortie_dict['y'] = y
    sortie_dict['numWeaponsDelivered'] = sortie[2]
    sortie_dict['weaponTypeWeightKg'] = sortie[4] / 2.2046
    sortie_dict['date'] = sortie[3]
    sortie_dict['weaponTypeIronKg'] = sortie_dict['weaponTypeWeightKg'] * 0.41
    sortie_dict['explosiveWeightKg'] = sortie_dict['weaponTypeWeightKg'] * 0.46
    sortie_dict['FeWashable'] = sortie_dict['weaponTypeIronKg'] * sortie_dict['numWeaponsDelivered'] * 0.0089
    sortie_dict['FeSuspended'] = sortie_dict['weaponTypeIronKg'] * sortie_dict['numWeaponsDelivered'] * 0.0177
    sortie_dict['FeBedded'] = sortie_dict['weaponTypeIronKg'] * sortie_dict['numWeaponsDelivered'] * 0.9734

    sortieYearLists[year].append(sortie_dict)
  
  # all_sorties = []
  # for year in sortieYearLists:
  #   for sortie in year:
  #     all_sorties.append(sortie)
  
  for i, year in enumerate(sortieYearLists):
    print(f'number of sorties in year {i}: {len(year)}')

  for i, year in enumerate(sortieYearLists):
    array = np.zeros((int(ymax_metric - ymin_metric)//cell_size, int(xmax_metric - xmin_metric)//cell_size))
    gaussianProcessor(array, year, name=f'Washable_{i}', raster_info={'cellsize': cell_size, 'x': xmin_metric, 'y': ymin_metric})

  # with concurrent.futures.ProcessPoolExecutor() as executor:
    # executor.map(staticProcessor, [array]*number_of_years, sortieYearLists, ['Bedded_' + str(i) for i in range(number_of_years)], ['FeBedded'] * number_of_years, [{'cellsize': cell_size, 'x': xmin_metric, 'y': ymin_metric} for i in range(number_of_years)])
    # executor.map(staticProcessor, [array]*number_of_years, sortieYearLists, ['Suspended_' + str(i) for i in range(number_of_years)], ['FeSuspended'] * number_of_years, [{'cellsize': cell_size, 'x': xmin_metric, 'y': ymin_metric} for i in range(number_of_years)])
    # executor.map(gaussianProcessor, [array]*number_of_years, sortieYearLists, ['Washable_' + str(i) for i in range(number_of_years)], [{'cellsize': cell_size, 'x': xmin_metric, 'y': ymin_metric} for i in range(number_of_years)])
  # staticProcessor(array, all_sorties, name='Bedded_all', static_type='FeBedded', raster_info={'cellsize': cell_size, 'x': xmin_metric, 'y': ymin_metric})
  # gaussianProcessor(array, sortieYearLists[0], name='Washable_0', raster_info={'cellsize': cell_size, 'x': xmin_metric, 'y': ymin_metric})


  print(f"Number of sorties: {sum([len(i) for i in sortieYearLists])}")

if __name__ == "__main__":
  main()