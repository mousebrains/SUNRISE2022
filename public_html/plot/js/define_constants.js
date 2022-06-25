// define some labels to be used by both the timeseries and Hovmoller plotters
// available data fields
const PELICAN_DATA_VARIABLES = [
  "Time",
  "Inertial Periods",
	"Latitude",
	"Longitude",
	"Salinity",
	"Temperature",
	// "Chlorophyll",
	"Air Temperature",
	"Air Pressure",
	"Relative Humidity",
	"Wind Speed",
	"Wind Direction",
	"Wind u",
	"Wind v"
];

const POINTSUR_DATA_VARIABLES = [
  "Time",
  "Inertial Periods",
	"Latitude",
	"Longitude",
	"Salinity",
	"Temperature",
	// "Chlorophyll",
	"Air Temperature",
	"Air Pressure",
	"Relative Humidity",
	"Wind Speed",
	"Wind Direction",
	"Wind u",
	"Wind v"
];

const LABELS = {
  "None": "",
  "Time": "Time",
  "Inertial Periods": "Time [ Inertial Periods ]",
  "Latitude": "Latitude [ \u00B0N ]",
  "Longitude": "Longitude [ \u00B0E ]",
  "Salinity": "Salinity [ PSU ]",
  "Temperature": "Temperature [ \u00B0C ]",
  "Chlorophyll": "Chlorophyll [ \u03BCg/L ]",
  "U - Slab Model": "U [ m<sup>2</sup>/s ]",
  "V - Slab Model": "V [ m<sup>2</sup>/s ]",
  "Air Temperature": "Air Temperature [ \u00B0C ]",
	"Air Pressure": "Air Pressure [ mbar ]",
	"Relative Humidity": "Relative Humidity [ % ]",
	"Wind Speed": "Wind Speed [ m/s ]" ,
	"Wind Direction": "Wind Direction [ \u00B0 ]",
  "Wind u": "Wind u [ m/s ]",
  "Wind v": "Wind v [ m/s ]"
}
