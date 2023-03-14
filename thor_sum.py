import csv
import pprint
import arcpy
import os

with open("THOR_processed.csv", "r", encoding="UTF-8") as thor_utf:
    # list column names
    reader = csv.reader(thor_utf)
    header = next(reader)
    # pretty print column names
    pprint.pprint(header)

    totalWeaponsDelivered = 0
    totalWeaponsDeliveredWeight = 0
    sortieCount = 0

    # loop thor_utf
    for row in reader:
        # print(row)
        # print(row[header.index("NumWeaponsDelivered")])
        # print(row[header.index("WeaponsDeliveredWeight")])
        totalWeaponsDelivered += int(row[header.index("NumWeaponsDelivered")])
        totalWeaponsDeliveredWeight += (int(row[header.index("WeaponTypeWeight")]) * int(row[header.index("NumWeaponsDelivered")]))
        sortieCount += 1

    print(f"Total Weapons Delivered: {totalWeaponsDelivered}")
    print(f"Total Weapons Delivered Weight: {totalWeaponsDeliveredWeight}")
    print(f"Total Sorties: {sortieCount}")
        
    
    
current_folder = os.path.dirname(os.path.abspath(__file__))
arcpy.env.workspace = current_folder + "/MyProject/MyProject.gdb"
dataset = 'namsouydataset'
sortieCursor = arcpy.da.SearchCursor(dataset, ['NumWeaponsDelivered', 'WeaponTypeWeight' ])

namsouy_totalWeaponsDelivered = 0
namsouy_totalWeaponsDeliveredWeight = 0
sortieNamSouyCount = 0

for row in sortieCursor:
    namsouy_totalWeaponsDelivered += row[0]
    namsouy_totalWeaponsDeliveredWeight += (row[1] * row[0])
    sortieNamSouyCount += 1

print(f"Total Weapons Delivered: {namsouy_totalWeaponsDelivered}")
print(f"Total Weapons Delivered Weight: {namsouy_totalWeaponsDeliveredWeight}")
print(f"Total Sorties: {sortieNamSouyCount}")

# write the above to an output file called thor_sum.txt
with open("thor_sum.txt", "w") as f:
    f.write(f"Total Weapons Delivered: {totalWeaponsDelivered}\n")
    f.write(f"Total Weapons Delivered Weight: {totalWeaponsDeliveredWeight}\n")
    f.write(f"Total Sorties: {sortieCount}\n")
    f.write(f"Total Namsouy Weapons Delivered: {namsouy_totalWeaponsDelivered}\n")
    f.write(f"Total Namsouy Weapons Delivered Weight: {namsouy_totalWeaponsDeliveredWeight}\n")
    f.write(f"Total Namsouy Sorties: {sortieNamSouyCount}\n")