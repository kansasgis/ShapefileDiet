#-------------------------------------------------------------------------------
# Name:        ShapefileDiet
# Purpose:     Creates a "skinny" version of a shapefile with field lengths
#               that are appropriate for the value lengths
#
# NOTE:        Since shapefiles don't do nulls, null values are converted:
#               text = ''
#               numbers = 0
#               date = 12/31/1899, 12:00 AM
#
#
# Author:      Kristen Jordan Koenig, Kansas Data Access and Support Center
#
# Created:     April 2017
# Copyright:   (c) Kristen Jordan Koenig 2017
#-------------------------------------------------------------------------------
from arcpy import (ListFields, GetParameterAsText, CreateTable_management,
        AddField_management, Exists, AddMessage, DeleteRows_management,
        CreateFeatureclass_management, Append_management, Describe,
        Delete_management, MakeFeatureLayer_management, GetCount_management,
        AddWarning)
from arcpy.da import SearchCursor, InsertCursor
from os.path import dirname, basename, join
import datetime


def ListFieldNames(item):
    # create a list of field names
    fields = ListFields(item)
    fieldList = []
    for f in fields:
        fieldList.append(f.name.upper())
    return fieldList


def fieldExists(fc, fieldName):
    # see if a field exists in a feature class or table
    exists = False
    fields = ListFieldNames(fc)
    if fieldName in fields:
        exists = True
    return exists


def getFastCount(lyr):
    # return a fast count of records
    result = GetCount_management(lyr)
    count = int(result.getOutput(0))
    return count


def userMessage(stuff):
    # print something regardless of platform
    AddMessage(stuff)
    print(stuff)


def makeRow(out_fc, insert_fields, row_value, numFieldsIndexList,
                dateFieldsIndexList):
    # cleans up row values, creates a row

    # clean up row values first
    list_row = list(row_value)
    for index, item in enumerate(list_row):
        # if the value is null, deal with it
        if item is None:
            if index in numFieldsIndexList:
                list_row[index] = 0
            elif index in dateFieldsIndexList:
                fake_date = datetime.datetime(1899, 12, 30, 0, 0)
                list_row[index] = fake_date
            else:
                list_row[index] = ""

    # insert the cleaned row into the output feature class
    cursor = InsertCursor(out_fc, insert_fields)
    cursor.insertRow(tuple(list_row))
    del cursor


def main():
    fc = GetParameterAsText(0)
    out_table = GetParameterAsText(1)
    out_fc = GetParameterAsText(2)

    for thingy in [out_table, out_fc]:
        if Exists(thingy):
            Delete_management(thingy)


    # --------------set up reporting table for new field names-----------------
    field_name = "PRENAME"
    field_count = "NEWCOUNT"
    schema_count = "PRECOUNT"
    new_name = "NEWNAME"

    #see if the output table exists
    if not Exists(out_table):
        CreateTable_management(dirname(out_table), basename(out_table))
    else:
        DeleteRows_management(out_table)

    #see if fields already exist, if not, create them
    if not fieldExists(out_table, field_name):
        AddField_management(out_table, field_name, "TEXT", "", "", 30)

    if not fieldExists(out_table, schema_count):
        AddField_management(out_table, schema_count, "LONG")

    if not fieldExists(out_table, field_count):
        AddField_management(out_table, field_count, "SHORT")

    if not fieldExists(out_table, new_name):
        AddField_management(out_table, new_name, "TEXT", "", "", 10)

    # loop through all fields
    all_fields = ListFields(fc)

    # create name dictionary of shortened shapefile names
    name_dictionary = {}
    shortList = [] # necessary for flagging repeated field names

    for fn in all_fields:
        short_name = fn.name
        if len(fn.name) > 10:
            short_name = fn.name[0:10]

        # make sure the shortened field name doesn't already exists
        if short_name not in shortList:
            shortList.append(short_name)
            name_dictionary[fn.name] = short_name
        else:
            i = 0
            while short_name in shortList and i < 100:
                short_name = short_name[0:7] + "_" + str(i)
                i += 1
            name_dictionary[fn.name] = short_name
            shortList.append(short_name)

    # -----next step, create new feature class & add all fields----------------
    # -----for text fields, make the length the proper length------------------

    desc = Describe(fc)
    geom_type = desc.shapeType
    SR = desc.spatialReference

    # create new feature class
    CreateFeatureclass_management(dirname(out_fc), basename(out_fc), geom_type,
                "", "", "", SR)

    # create list to hold the names of number fields (used later)
    numFields = []
    dateFields = []

    # get the name of the OID field while looping
    oid = ""

    # loop through string fields
    for f in all_fields:
        short_name = name_dictionary[f.name]
        data_type = f.type.upper()

        # check to see if the data type is "normal"
        if data_type in ["TEXT", "FLOAT", "DOUBLE", "SHORT", "LONG", "DATE",
                        "BLOB", "RASTER", "GUID", "STRING", "INTEGER",
                        "SMALLINTEGER"]:

            # special track for string fields
            if data_type in ["STRING", "TEXT"]:

                # set counter at 0
                i = 0

                # set up search cursor on feature class just on that field
                with SearchCursor(fc, (f.name)) as rows:
                    for row in rows:
                        if row[0] is not None:
                            # loop through values to get the longest length
                            if len(row[0]) > i:
                                i = len(row[0])

                # make sure i isn't bigger than 254
                if i > 254:
                    i = 254

                # at this point, i equals the length of the longest field entry

                # insert the field name and the length into the output table
                cursor = InsertCursor(out_table, (field_name, field_count,
                        schema_count, new_name))
                new_row = (f.name, i, f.length, short_name)
                cursor.insertRow(new_row)

                del row, rows, cursor, new_row

                # add a row to the new feature class
                AddField_management(out_fc, short_name, "TEXT", "", "", i)

            # track for numbers, GUIDs & dates
            else:
                AddField_management(out_fc, short_name, data_type)

                # if it's a number, record the field name in the num field list
                if data_type in ["SHORT", "LONG", "INTEGER", "FLOAT", "DOUBLE"]:
                    numFields.append(f.name)
                elif data_type in ["DATE"]:
                    dateFields.append(f.name)

                #make sure all fields are in the translation table
                cursor = InsertCursor(out_table, (field_name, new_name))
                new_row = (f.name, short_name)
                cursor.insertRow(new_row)
                del cursor, new_row

        elif data_type == "OID":
            AddField_management(out_fc, "LinkOID", "INTEGER")
            name_dictionary[f.name] = "LinkOID" # add for field mapping
            oid = f.name

            # add link field for object ID to the mapping table
            cursor = InsertCursor(out_table, (field_name, new_name))
            new_row = (f.name, "LinkOID")
            cursor.insertRow(new_row)
            del cursor, new_row
        elif data_type == "GEOMETRY":
            pass
        else:
            print("Field " + f.name + " is type " + f.type + ". It will not be copied over.")
            AddWarning("Field " + f.name + " is type " + f.type + ". It will not be copied over.")
            del name_dictionary[f.name]

    # -----copy data into the new FC-------------------------------------------

    # set up field lists for search & insert cursors
    oldFields, newFields = [], []

    for field in name_dictionary.keys():
        oldFields.append(field)
        newFields.append(name_dictionary[field])

    # set up a text only version of the fields
    oldFieldsTextOnly = tuple(oldFields)
    newFieldsTextOnly = tuple(newFields)

    # add SHAPE to the original set of fields
    oldFields.append("SHAPE@")
    newFields.append("SHAPE@")

    # convert the new field list to a tuple, safety first
    newFields = tuple(newFields) # this is the one with the shape field

    # create a list of the indexes of number & date fields
    numFieldsIndexList, dateFieldsIndexList = [], []
    for numF in numFields:
        numFieldsIndexList.append(oldFields.index(numF))
    for dateF in dateFields:
        dateFieldsIndexList.append(oldFields.index(dateF))

    # ran into an issue with invalid geometry, so here's the workaround
    invalidDict = {"point": 1, "polyline": 2, "polygon":3}

    # set up reporting for records that didn't copy
    didNotCopy = []

    # fill new rows with old rows
    with SearchCursor(fc, oldFields) as rows:
        for row in rows:
            geomIndex = oldFields.index("SHAPE@")
            geom = row[geomIndex]
            objectID = str(row[oldFields.index(oid)])
            try:

                try:
                    # find the minimum number of required points
                    minNum = invalidDict[geom_type.lower()]

                    # get the count of points in the geometry
                    count = geom.pointCount

                    # if the count is smaller than the minimum number, there's a problem
                    if count < minNum:
                        wc = oid + " = " + objectID
                        # here, we won't copy the geometry, only the fields
                        userMessage("count smaller than min")
                        with SearchCursor(fc, oldFieldsTextOnly, wc) as rows2:
                            for row2 in rows2:
                                makeRow(out_fc, newFieldsTextOnly, row2, numFieldsIndexList, dateFieldsIndexList)
                        del row2, rows2, wc

                    else:
                        # excellent, the record is normal & will copy
                        makeRow(out_fc, newFields, row, numFieldsIndexList, dateFieldsIndexList)

                except Exception as e:
                    userMessage(str(e))
                    # if we're in this area, it means the record has no geometry
                    wc = oid + " = " + objectID
                    with SearchCursor(fc, oldFieldsTextOnly, wc) as rows2:
                        for row2 in rows2:
                            makeRow(out_fc, newFieldsTextOnly, row2, numFieldsIndexList, dateFieldsIndexList)
                    del row2, rows2, wc


            except Exception as e:
                userMessage(str(e))
                # for whatever reason, the record did not copy
                userMessage("Error copying record ObjectID " + objectID)
                didNotCopy.append(objectID)

    if didNotCopy != []:
        userMessage("These records did not copy- %s %s" % (oid, ", ".join(didNotCopy)))

    userMessage("Skinny shapefile complete.")

if __name__ == '__main__':
    main()
