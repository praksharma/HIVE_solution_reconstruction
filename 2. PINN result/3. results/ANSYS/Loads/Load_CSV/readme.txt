1. FInd ERMES.rmed from the output of pre aster
2. Set Paraview->Tools->manage Plugins
3. Click arrow next to MEDReader and check "Auto Load".
4. Now open ERMES.rmed in paraview, using "paraview ERMES.rmed" in the terminal.
5. Now we need to extract the HIVE sample from the entire geometry.
6. Once you "Apply" the entire geometry, Go to Filters->Alphabetic-> Extract Group . Found in the second column.


To extract the coordinates and value of "joule_heating".
1. Open a new layout and select "spreadsheet view".

2. In the spreadsheet view select
	Showing = "ExtractGroup1"
	Attribute = "Point Data"
	Precision = 6
	
3. Click "Toggle column visibility" and only select "Points" and "joule_heating".
4. Click the last button in spreadsheet view to export the csv file.
