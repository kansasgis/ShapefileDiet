Name:        Shapefile Diet
Purpose:     Creates a "skinny" version of a shapefile with field lengths
               that are appropriate for the value lengths. Example: a 
	       string field is defined as being 200 characters, but the 
	       longest attribute is only 54 characters. The output 
	       shapefile's matching field will be defined as 54 characters
	       long. 
	       
	       This tool can drastically decrease the amount of space
	       the shapefile uses on disk.

	       See the output field map for all field details.

NOTE:        Since shapefiles don't do nulls, null values are converted:
              text = ''
              numbers = 0
              date = 12/31/1899, 12:00 AM


Author:      Kristen Jordan Koenig, Kansas Data Access and Support Center


Output Field Map:
	PRENAME- previous field name
	PRECOUNT- previous field length	
	NEWCOUNT- new field length (calculated by longest attribute length)
	NEWNAME- new field name
