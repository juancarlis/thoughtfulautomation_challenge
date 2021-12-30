# Challenge solution


#### My solution for the ThoughtfulAutomation RPA Challenge
[See challenge description here.](Challenge_Description.md)

#### Config
Modify **config/config.yaml** for basic configuration:
- agency: to select the agency whose "Individual Investments" are going to be scraped. 
- pdf_path: the path where PDF files are going to be downloaded.


#### Improvements
- Change Sleep function with selenium explicit waits. 
- Excel file gets corrupted when exporting PDF comparison into the existing worksheet (with the name of the agency).
