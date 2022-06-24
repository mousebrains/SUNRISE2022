// main script for the hovmoller plots

//first run utils.js, toggle_collpasable.js, and constants.js

// *********************************************** //
// ************** INITIALISE THE UI*************** //
// *********************************************** //

const COMMON_VARIABLES = PELICAN_DATA_VARIABLES.filter(x => POINTSUR_DATA_VARIABLES.includes(x));

// fill in data selector options
const x_axis_variable_selector = document.getElementById("x-axis-variable-select");
COMMON_VARIABLES.forEach(data_field => {
	let new_element = document.createElement('option');
	new_element.value = data_field;
	new_element.innerHTML = data_field;
	x_axis_variable_selector.appendChild(new_element);
});

const y_axis_variable_selector = document.getElementById("y-axis-variable-select");
COMMON_VARIABLES.forEach(data_field => {
	let new_element = document.createElement('option');
	new_element.value = data_field;
	new_element.innerHTML = data_field;
	y_axis_variable_selector.appendChild(new_element);
});

const Pelican_options_selector = document.getElementById("data-variable-PE-select");
PELICAN_DATA_VARIABLES.forEach(data_field => {
	if (data_field == "Time") { return }; // time breaks the colourbar
	let new_element = document.createElement('option');
	new_element.value = data_field;
	new_element.innerHTML = data_field;
	Pelican_options_selector.appendChild(new_element);
});

const PointSur_options_selector = document.getElementById("data-variable-PS-select");
POINTSUR_DATA_VARIABLES.forEach(data_field => {
	if (data_field == "Time") { return }; // time breaks the colourbar
	let new_element = document.createElement('option');
	new_element.value = data_field;
	new_element.innerHTML = data_field;
	PointSur_options_selector.appendChild(new_element);
});

// set user input preferences from localStorage
// list of ids of all preferences that have a value
const PREFERENCES_VALUES = [
	"x-axis-variable-select",
	"y-axis-variable-select",
	"data-variable-PE-select",
	"data-variable-PS-select",
	"figure-background-colour",
	"data-PE-colour-map",
	"data-PE-min",
	"data-PE-max",
	"data-PS-colour-map",
	"data-PS-min",
	"data-PS-max"
];

// list of ids of all preferences that are checkboxes or radio groups
const PREFERENCES_CHECKBOXES = [
	"figure-x-axis-grid",
	"figure-x-axis-reversed",
	"figure-y-axis-grid",
	"figure-y-axis-reversed",
	"data-PE-reverse-colour-map",
	"data-PS-reverse-colour-map",
	"1min-resolution",
	"5min-resolution",
	"15min-resolution"
];

setPreferences()

// *********************************************** //
// *************** UI INITIALISED **************** //
// *********** NOW INITIALISE PLOTTING *********** //
// *********************************************** //

// create an object to read set data values into and pass to php
const set_data_values = {
	x_variable: 'None',
	y_variable: 'None',
	data_PE: 'None',
	data_PS: 'None',
};
updateSetData();

let now = new Date();
let earlier = new Date();
earlier.setHours(now.getHours()-4);

// create an object to read time values into and pass to php
// also set the edfault range to now - 2 hours to now, datetime2str defined in js/utils.js
const set_time_values = {
	start_time: datetime2str(earlier),
	end_time: datetime2str(now),
	time_resolution: 1
};

// set default values in the time selectors
let start_time = document.getElementById("start-time");
start_time.value = set_time_values.start_time;
let end_time = document.getElementById("end-time");
end_time.value = set_time_values.end_time;

updateSetTime();


// set default values for figure settings
// modifying the figure setting modifies the layout
const figure_settings_values = {};
updateFigureSettings()

// define 2 datasets that hold data
const dataset_PE = {	name: '',	x_data: [], y_data: [], c_data: [] };
const dataset_PS = {	name: '',	x_data: [], y_data: [], c_data: [] };

// set default colour maps
// modifying these properties modifies the data colour maps
var PE_colour_properties = {};
var PS_colour_properties = {};
updateColourProperties()



// get the div containing the plot
const hovmoller_plot = document.getElementById('hovmoller-plot');

//initialise the plot
let plot_data = [
	{
		x: [],
		y: [],
		name: '',
		type: 'scatter',
		mode: 'markers',
		marker: {'color': [], colorscale: 'YlGnBu'},
		showlegend: false,
		hovertemplate: "%{xaxis.title.text}: %{x}<br>" +
            			 "%{yaxis.title.text}: %{y}<br>" +
            			 "%{fullData.name}: %{marker.color}<br>" +
									 "<extra></extra>"
	}, {
		x: [],
		y: [],
		name: '',
		type: 'scatter',
		mode: 'markers',
		marker: {'color': [] , colorscale: 'YlGnBu'},
		showlegend: false,
		hovertemplate: "%{xaxis.title.text}: %{x}<br>" +
            			 "%{yaxis.title.text}: %{y}<br>" +
									 "%{fullData.name}: %{marker.color}" +
									 "<extra></extra>"
	}
];

let layout = {
	title: {text: '', font: {color: 'white'}},
	margin: { l: 70, r: 70, b: 70, t: 50, pad: 4 },
};


let config = {
	margin: { t: 0, l: 0, r: 0, b: 0},
	editable: true,
	modeBarButtonsToRemove: ['lasso2d','select2d'],
	toImageButtonOptions: {filename: 'hovmoller'},
	scrollZoom: true,
	displaylogo: false
};

// initialise the plot and attach the resize observer when created
Plotly.newPlot(hovmoller_plot, plot_data,	layout, config)
.then(function(gd) { plotObserver.observe(gd); })
.then(modifyAxesProperties());

// This observer resizes the plot whenever its container resizes
const plotObserver = new ResizeObserver(entries => {
	for (let entry of entries) {
    Plotly.Plots.resize(entry.target);
}});

// Set labels to ''
setLabels('','');

// *********************************************** //
// *********** FINISHED INITIALISATION *********** //
// *********** NOW DEFINE FUNCTIONS    *********** //
// *********************************************** //

// ** DEFINE NEW MIN AND MAX FUNCTIONS TO HANDLE NULL VALUES

const my_min = (values) => values.reduce((m, v) => (v != null && v < m ? v : m), Infinity);
const my_max = (values) => values.reduce((m, v) => (v != null && v > m ? v : m), -Infinity);


// ** FIRST FUNCTIONS FOR READING DATA FROM THE PAGE ** //

// update figure settings values
function updateFigureSettings() {
	var figure_background_colour = document.getElementById("figure-background-colour").value;
	var figure_x_axis_gridlines = document.getElementById("figure-x-axis-grid").checked;
	var figure_x_axis_reverse = document.getElementById("figure-x-axis-reversed").checked;
	var figure_y_axis_gridlines = document.getElementById("figure-y-axis-grid").checked;
	var figure_y_axis_reverse = document.getElementById("figure-y-axis-reversed").checked;
	figure_settings_values.background_colour = figure_background_colour;
	figure_settings_values.x_axis_gridlines = figure_x_axis_gridlines;
	figure_settings_values.x_axis_reverse = figure_x_axis_reverse;
	figure_settings_values.y_axis_gridlines = figure_y_axis_gridlines;
	figure_settings_values.y_axis_reverse = figure_y_axis_reverse;
};

// update axes properties values
function updateColourProperties() {
	var PE_colourmap = document.getElementById('data-PE-colour-map').value;
	var PE_reverse = document.getElementById('data-PE-reverse-colour-map').checked;
	var PE_min = document.getElementById('data-PE-min').value;
	var PE_max = document.getElementById('data-PE-max').value;
	var PS_colourmap = document.getElementById('data-PS-colour-map').value;
	var PS_reverse = document.getElementById('data-PS-reverse-colour-map').checked;
	var PS_min = document.getElementById('data-PS-min').value;
	var PS_max = document.getElementById('data-PS-max').value;

	if ((PE_min === "") && (PE_max === "") && (PS_min === "") && (PS_max === "")
		&& (dataset_PE.name === dataset_PS.name)) {
		//PE_min = Math.min(...dataset_PE.c_data,...dataset_PS.c_data);
		PE_min = my_min(dataset_PE.c_data.concat(dataset_PS.c_data));
		PS_min = PE_min;
		//PE_max = Math.max(...dataset_PE.c_data,...dataset_PS.c_data);
		PE_max = my_max(dataset_PE.c_data.concat(dataset_PS.c_data));
		PS_max = PE_max;
	} else {
		// if ((PE_min === "") || isNaN(PE_min)) { PE_min = Math.min(...dataset_PE.c_data) };
		// if ((PE_max === "") || isNaN(PE_max)) { PE_max = Math.max(...dataset_PE.c_data) };
		// if ((PS_min === "") || isNaN(PS_min)) { PS_min = Math.min(...dataset_PS.c_data) };
		// if ((PS_max === "") || isNaN(PS_max)) { PS_max = Math.max(...dataset_PS.c_data) };
		if ((PE_min === "") || isNaN(PE_min)) { PE_min = my_min(dataset_PE.c_data) };
		if ((PE_max === "") || isNaN(PE_max)) { PE_max = my_max(dataset_PE.c_data) };
		if ((PS_min === "") || isNaN(PS_min)) { PS_min = my_min(dataset_PS.c_data) };
		if ((PS_max === "") || isNaN(PS_max)) { PS_max = my_max(dataset_PS.c_data) };
	};

	PE_colour_properties = {
		colourmap: PE_colourmap,
		reverse: PE_reverse,
		min: PE_min,
		max: PE_max
	};
	PS_colour_properties = {
		colourmap: PS_colourmap,
		reverse: PS_reverse,
		min: PS_min,
		max: PS_max
	};
};

// update set_data_values
function updateSetData() {
	var new_x_variable = document.getElementById("x-axis-variable-select").value;
	var new_y_variable = document.getElementById("y-axis-variable-select").value;
	var new_data_PE_variable = document.getElementById("data-variable-PE-select").value;
	var new_data_PS_variable = document.getElementById("data-variable-PS-select").value;
	set_data_values.x_variable = new_x_variable;
	set_data_values.y_variable = new_y_variable;
	set_data_values.data_PE = new_data_PE_variable;
	set_data_values.data_PS = new_data_PS_variable;
};

// update set_time_values
function updateSetTime() {
	var new_start_time = document.getElementById("start-time").value;
	var new_end_time = document.getElementById("end-time").value;
	var new_time_resolution = document.querySelector('input[name="time-resolution"]:checked').value;
	set_time_values.start_time = new_start_time;
	set_time_values.end_time = new_end_time;
	set_time_values.time_resolution = new_time_resolution;
};

// ******************************************************** //
// *********** FUNCTIONS FOR MODIFYING THE PLOT *********** //
// ******************************************************** //

// define a function that converts the datasets into a data_update object for plotly
// called when new data is loaded
function dataUpdate() {
	var data_update = {
		x: [dataset_PE.x_data, dataset_PS.x_data],
		y: [dataset_PE.y_data, dataset_PS.y_data],
		'marker.color': [dataset_PE.c_data, dataset_PS.c_data],
		name: [dataset_PE.name, dataset_PS.name]
	};

	return data_update
	};

// modify the plot data
// called when new data is loaded
async function replotData() {
	var data_update = dataUpdate();
	await Plotly.restyle(hovmoller_plot,data_update);
};

// a function that returns a plotly layout update and data colour update
function axesUpdate() {
	let bg_colour = hex2plotlyRGB(figure_settings_values.background_colour);
	var data_update = {
		'marker.colorscale': [PE_colour_properties.colourmap, PS_colour_properties.colourmap],
		'marker.cmin': [ PE_colour_properties.min, PS_colour_properties.min	],
		'marker.cmax': [ PE_colour_properties.max, PS_colour_properties.max ],
		'marker.reversescale': [PE_colour_properties.reverse, PS_colour_properties.reverse]
	};

	// set the title and independent axis
	var layout_update = {
		plot_bgcolor: bg_colour,
		'xaxis.showgrid': figure_settings_values.x_axis_gridlines,
		'xaxis.autorange': figure_settings_values.x_axis_reverse ? 'reversed' : true,
		'yaxis.showgrid': figure_settings_values.y_axis_gridlines,
		'yaxis.autorange': figure_settings_values.y_axis_reverse ? 'reversed' : true
	};

	return [data_update, layout_update]
}


// modify the plot properties
// called when Apply Changes is clicked
async function modifyAxesProperties() {
	[data_update, layout_update] = axesUpdate();
	await Plotly.update(hovmoller_plot,data_update,layout_update);
}

// function to modify the labels
// called when new data is loaded
async function setLabels(x_label,y_label) {
	var layout_update = {
		'xaxis.title': x_label,
		'yaxis.title': y_label
	};
	await Plotly.relayout(hovmoller_plot,layout_update);
};

// function to set colourbar and colourbar title
// called when new data is loaded
async function setColourbar(data_PE,data_PS) {
	if (data_PE == 'None') {
		PE_update = null;
	} else {
		PE_update = {
			'title': {text: LABELS[data_PE] || '', side: 'right'},
			'len': 0.5,
			'y': 1,
			'yanchor': 'top',

		};
	}
	if (data_PS == 'None') {
		PS_update = null;
	} else {
		PS_update = {
			'title': {text: LABELS[data_PS] || '', side: 'right'},
			'len': 0.5,
			'y': 0,
			'yanchor': 'bottom'
		};
	}

	// get the colourbar settings from axesUpdate
	// cmin and cmax may have been updated when new data was loaded
	var [data_update, layout_update] = axesUpdate();
	Object.assign(data_update, {'marker.colorbar': [PE_update, PS_update]});

	await Plotly.restyle(hovmoller_plot,data_update);
}


// ******************************************************** //
// ********** SAVE PREFERENCES TO LOCAL STORAGE *********** //
// ******************************************************** //

function getPreferences() {
	let preferences = {};
	PREFERENCES_VALUES.forEach(id => {
		let element = document.getElementById(id);
		preferences[id] = element.value;
	});
	PREFERENCES_CHECKBOXES.forEach(id => {
		let element = document.getElementById(id);
		preferences[id] = element.checked;
	});
	return preferences
};

function setPreferences() {
	PREFERENCES_VALUES.forEach(id => {
		let value = localStorage.getItem(id);
		if (value === null) {return};
		let element = document.getElementById(id);
		element.value = value;
	});
	PREFERENCES_CHECKBOXES.forEach(id => {
		let checked = localStorage.getItem(id);
		let element = document.getElementById(id);
		switch (checked) {
			case 'true':
				element.checked = true; break;
			case 'false':
				element.checked = false; break;
		}
	});
};

// ******************************************************** //
// ******************** ACTION BUTTONS ******************** //
// ******************************************************** //

// function called when "Apply Changes" Button is clicked
function applyChanges() {
	updateFigureSettings()
	updateColourProperties()
	modifyAxesProperties()
};

// function called when "Save Preferences" Button is clicked
function savePreferences() {
	let preferences = getPreferences()
	Object.entries(preferences).forEach(([key,value]) => {
		localStorage.setItem(key,value)
	});
};

// function called when "Clear Preferences" Button is clicked
function clearPreferences() {
	PREFERENCES_VALUES.forEach(id => localStorage.removeItem(id))
	PREFERENCES_CHECKBOXES.forEach(id => localStorage.removeItem(id))
};
