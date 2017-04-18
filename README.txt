Name:        Shapefile Diet
Purpose:     Creates a "skinny" version of a shapefile with field lengths
               that are appropriate for the value lengths

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
