// define some constants to be used by both the timeseries and Hovmoller plotters

// available data fields
const PELICAN_DATA_VARIABLES = [
  "Time",
//  "Inertial Periods",
	"Latitude",
	"Longitude",
	"Salinity",
	"Temperature",
//  "U - Slab Model",
//  "V - Slab Model"
];

const POINTSUR_DATA_VARIABLES = [
  "Time",
//  "Inertial Periods",
	"Latitude",
	"Longitude",
	"Salinity",
	"Temperature",
//  "U - Slab Model",
//  "V - Slab Model"
];

const LABELS = {
  "None": "",
  "Time": "Time",
  "Inertial Periods": "Time [ Inertial Periods ]",
  "Latitude": "Latitude [ \u00B0N ]",
  "Longitude": "Longitude [ \u00B0E ]",
  "Salinity": "Salinity [ PSU ]",
  "Temperature": "Temperature [ \u00B0C ]",
  "U - Slab Model": "U [ m<sup>2</sup>/s ]",
  "V - Slab Model": "V [ m<sup>2</sup>/s ]"
}
