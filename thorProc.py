
cols_removed_list = [n.strip() for n in (open("cols_removed.txt", "r")).readlines()]
# cols_removed_list.pop(-1)
print(cols_removed_list)
print(len(cols_removed_list))

col_index = []


thor = open("THOR_Vietnam_7_31_2013.csv", "r", encoding="UTF-8-SIG")
thor_utf = open("THOR_processed.csv", "w", encoding="UTF-8")
thor_coord = open("THOR_coords_only.csv", "w", encoding="UTF-8")


header_line = thor.readline().strip()
print(header_line)
header_list = header_line.split(",")
utf_header_list = []

for header in header_list:
  if header in cols_removed_list:
    utf_header_list.append(header)
    col_index.append(header_list.index(header))

thor_utf.write(f"{','.join(utf_header_list)}\n")
thor_coord.write(f"TgtLatDD_DDD_WGS84,TgtLonDDD_DDD_WGS84\n")



# 5 CountryFlyingMission       needs to be there
# 39 TgtCountry                laos, blank, null, unknown
# 51 NumWeaponsDelivered       not blank or zero
# 55 WeaponsDeliveredWeight    not blank or zero
# 78 WeaponTypeWeight          not blank or zero
# 81 TgtLatDD_DDD_WGS84        not blank or zero
# 84 TgtLonDDD_DDD_WGS84       not blank or zero
# 47 weaponType   
# 75 gunmissilebometype        not 0 or 4

CountryFlyingMission = 5
TgtCountry = 39
NumWeaponsDelivered = 51
WeaponsDeliveredWeight = 55
WeaponTypeWeight = 78
TgtLatDD_DDD_WGS84 = 81
TgtLonDDD_DDD_WGS84 = 84
weaponType = 47
gunMissileBombType = 75

zero = ["", "0", "null"]

weapon_ammo_pair_list = []

print(col_index)

for i in col_index:
  print(f"{i} {header_list[i]}")

flush_count = 0
line_count = 0

latlong_values = []

float_count = 0

for line in thor:
  # input()
  line_count += 1
  if line_count % 1000 == 0:
    print(f"processed {line_count} lines")
  line_list = line.split(",")
  dontSkip = True

  # getting possible values of latlong
  try:
    float(line_list[TgtLatDD_DDD_WGS84])
    float(line_list[TgtLonDDD_DDD_WGS84])
    float_count += 1
  except Exception as ex:
    pass
  
  try:
    float(line_list[TgtLonDDD_DDD_WGS84])
  except Exception as ex:
    if line_list[TgtLonDDD_DDD_WGS84] not in latlong_values:
      latlong_values.append(line_list[TgtLonDDD_DDD_WGS84])


  if f"{line_list[weaponType]} {line_list[gunMissileBombType]}" not in weapon_ammo_pair_list:
    weapon_ammo_pair_list.append(f"{line_list[weaponType]} {line_list[gunMissileBombType]}")

  if line_list[CountryFlyingMission].strip().lower() == "":
    # print(f"CountryFlyingMission {line_list[CountryFlyingMission]}")
    dontSkip = False
  if line_list[TgtCountry].strip().lower() != "laos":
    # print(f"TgtCountry {line_list[TgtCountry]}")
    dontSkip = False
  if line_list[NumWeaponsDelivered].strip().lower() in zero:
    # print(f"NumWeaponsDelivered {line_list[NumWeaponsDelivered]}")
    dontSkip = False
  if line_list[WeaponsDeliveredWeight].strip().lower() in zero:
    # print(f"WeaponsDeliveredWeight {line_list[WeaponsDeliveredWeight]}")
    dontSkip = False
  if line_list[WeaponTypeWeight].strip().lower() in zero:
    # print(f"WeaponTypeWeight {line_list[WeaponTypeWeight]}")
    dontSkip = False
  if line_list[TgtLatDD_DDD_WGS84].strip().lower() in zero:
    # print(f"TgtLatDD_DDD_WGS84 {line_list[TgtLatDD_DDD_WGS84]}")
    dontSkip = False
  if line_list[TgtLonDDD_DDD_WGS84].strip().lower() in zero:
    # print(f"TgtLonDDD_DDD_WGS84 {line_list[TgtLonDDD_DDD_WGS84]}")
    dontSkip = False
  if line_list[gunMissileBombType] in ["0", "4"]:
    dontSkip = False

  if dontSkip:
    processed_line = []
    for index in col_index:
      processed_line.append(line_list[index])
      
    # print(f"{processed_line}")
    thor_utf.write(f"{','.join(processed_line)}")
    thor_coord.write(f"{line_list[TgtLatDD_DDD_WGS84]},{line_list[TgtLatDD_DDD_WGS84]}\n")
    flush_count += 1
    if flush_count == 1000:
      thor_utf.flush()
      thor_coord.flush()
      flush_count = 0

print(latlong_values)
print(float_count)
  
# weaponAmmoFile = open("weaponAmmoPairs.txt", "w")

# for ammoPair in weapon_ammo_pair_list:
#   weaponAmmoFile.write(f"{ammoPair}\n")

# weaponAmmoFile.close()

# col_list = thor.readline().split(",")

# print(col_list.index("SourceID"))

# while 1:
#   print(thor.readline())
#   input()