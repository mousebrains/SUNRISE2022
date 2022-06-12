// main script for the timeseries plots

//first run utils.js, toggle_collpasable.js, and constants.js

// *********************************************** //
// ************** INITIALISE THE UI*************** //
// *********************************************** //

const COMMON_VARIABLES = PELICAN_DATA_VARIABLES.filter(x => POINTSUR_DATA_VARIABLES.includes(x));

// fill in data selector options
const independent_variable_selector = document.getElementById("independent-variable-select");
COMMON_VARIABLES.forEach(data_field => {
	let new_element = document.createElement('option');
	new_element.value = data_field;
	new_element.innerHTML = data_field;
	independent_variable_selector.appendChild(new_element);
});

const Pelican_options_selector = Array.from(document.getElementsByClassName("Pelican-options"));
Pelican_options_selector.forEach(selector => {
	PELICAN_DATA_VARIABLES.forEach(data_field => {
		let new_element = document.createElement('option');
		new_element.value = 'PE '+data_field;
		new_element.innerHTML = 'PE '+data_field;
		selector.appendChild(new_element);
	});
});

const PointSur_options_selector = Array.from(document.getElementsByClassName("PointSur-options"));
PointSur_options_selector.forEach(selector => {
	POINTSUR_DATA_VARIABLES.forEach(data_field => {
		let new_element = document.createElement('option');
		new_element.value = 'PS '+data_field;
		new_element.innerHTML = 'PS '+data_field;
		selector.appendChild(new_element);
	});
});

// set user input preferences from localStorage
// list of ids of all preferences that have a value
const PREFERENCES_VALUES = [
	"independent-variable-select",
	"dependent-variable-1-select",
	"dependent-variable-2-select",
	"dependent-variable-3-select",
	"dependent-variable-4-select",
	"figure-background-colour",
	"data-1-colour",
	"data-2-colour",
	"data-3-colour",
	"data-4-colour"
];

// list of ids of all preferences that are checkboxes
const PREFERENCES_CHECKBOXES = [
	"figure-independent-axis-grid",
	"figure-independent-axis-reversed",
	"data-1-grid",
	"data-1-reversed",
	"data-2-grid",
	"data-2-reversed",
	"data-3-grid",
	"data-3-reversed",
	"data-4-grid",
	"data-4-reversed",
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
	independent_variable: 'None',
	data_1: 'None',
	data_2: 'None',
	data_3: 'None',
	data_4: 'None'
};
updateSetData();

let now = new Date();
let earlier = new Date();
earlier.setHours(now.getHours()-2);

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

// create a variable to determine whether the x axis is the independent axis or not
// switching the independent axis requires modifying both the layout and data
var independent_axis_x = true;

// set default values for figure settings
// modifying the figure setting modifies the layout
const figure_settings_values = {};
updateFigureSettings()

// set default property values for each axes
// modifying these properties modifies the layout and data color
// this is agnostic to which axis is independent
const axes_properties = [{},{},{},{}];
updateAxesProperties()

// define 4 datasets that hold data
// this is agnostic to which axis is independent
const datasets = [
	{	name: '',	independent: [], dependent: [] },
	{	name: '',	independent: [], dependent: [] },
	{	name: '',	independent: [], dependent: [] },
	{	name: '',	independent: [], dependent: [] }
]

// get the div containing the plot
const timeseries_plot = document.getElementById('timeseries-plot');

//initialise the plot
let plot_data = [
	{	x: [], y: [], name: '', type: 'scatter', xaxis: 'x', yaxis: 'y' },
	{	x: [], y: [], name: '', type: 'scatter', xaxis: 'x', yaxis: 'y2' },
	{	x: [], y: [], name: '', type: 'scatter', xaxis: 'x', yaxis: 'y3' },
	{	x: [], y: [], name: '', type: 'scatter', xaxis: 'x', yaxis: 'y4' },
];

let layout = {
	title: {text: '', font: {color: 'white'}},
	margin: { l: 70, r: 70, b: 70, t: 50, pad: 4 },
	xaxis: {domain: [0.1, 0.9]},
	yaxis: {anchor: 'x', overlaying: null, side: 'left', position: 0},
	yaxis2: {anchor: 'x', overlaying: 'y', side: 'right', position: 1},
	yaxis3: {anchor: 'free', overlaying: 'y', side: 'left', position: 0.05},
	yaxis4: {anchor: 'free', overlaying: 'y', side: 'right', position: 0.95},
	legend: {x: 0.1, y: 1, xanchor: 'left', yanchor: 'top', bgcolor: 'rgba(255,255,255,0.5)'}
};


let config = {
	margin: { t: 0, l: 0, r: 0, b: 0},
	editable: true,
	modeBarButtonsToRemove: ['lasso2d','select2d'],
	toImageButtonOptions: {filename: 'timeseries'},
	scrollZoom: true,
	displaylogo: false
};

// initialise the plot and attach the resize observer when created
Plotly.newPlot(timeseries_plot, plot_data,	layout, config)
.then(function(gd) { plotObserver.observe(gd); })
.then(modifyAxesProperties());

// This observer resizes the plot whenever its container resizes
const plotObserver = new ResizeObserver(entries => {
	for (let entry of entries) {
    Plotly.Plots.resize(entry.target);
}});

// Set labels to ''
setLabels(independent_axis_x,'',['','','','']);

// *********************************************** //
// *********** FINISHED INITIALISATION *********** //
// *********** NOW DEFINE FUNCTIONS    *********** //
// *********************************************** //

// ** FIRST FUNCTIONS FOR READING DATA FROM THE PAGE ** //

// update figure settings values
function updateFigureSettings() {
	var figure_background_colour = document.getElementById("figure-background-colour").value;
	var figure_independent_axis_gridlines = document.getElementById("figure-independent-axis-grid").checked;
	var figure_independent_axis_reverse = document.getElementById("figure-independent-axis-reversed").checked;
	figure_settings_values.background_colour = figure_background_colour;
	figure_settings_values.independent_axis_gridlines = figure_independent_axis_gridlines;
	figure_settings_values.independent_axis_reverse = figure_independent_axis_reverse;
};

// update axes properties values
function updateAxesProperties() {
	for (let i = 0; i < 4; i++) {
	  var prefix = 'data-'+(i+1)+'-';
		var colour = document.getElementById(prefix+'colour').value;
		var gridlines = document.getElementById(prefix+'grid').checked;
		var reverse = document.getElementById(prefix+'reversed').checked;
		axes_properties[i] = {
			colour: colour,
			gridlines: gridlines,
			reverse: reverse
		}
	}
};

// update set_data_values
function updateSetData() {
	var new_independent_variable = document.getElementById("independent-variable-select").value;
	var new_data_1_variable = document.getElementById("dependent-variable-1-select").value;
	var new_data_2_variable = document.getElementById("dependent-variable-2-select").value;
	var new_data_3_variable = document.getElementById("dependent-variable-3-select").value;
	var new_data_4_variable = document.getElementById("dependent-variable-4-select").value;
	set_data_values.independent_variable = new_independent_variable;
	set_data_values.data_1 = new_data_1_variable;
	set_data_values.data_2 = new_data_2_variable;
	set_data_values.data_3 = new_data_3_variable;
	set_data_values.data_4 = new_data_4_variable;
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
function dataUpdate(independent_axis_x) {
	if (independent_axis_x) {
		var data_update = {
			x: datasets.map(ds => ds.independent),
			y: datasets.map(ds => ds.dependent),
			name: datasets.map(ds => ds.name),
			xaxis: ['x'],
			yaxis: ['y','y2','y3','y4']
		};
	} else {
		var data_update = {
			x: datasets.map(ds => ds.dependent),
			y: datasets.map(ds => ds.independent),
			name: datasets.map(ds => ds.name),
			xaxis: ['x','x2','x3','x4'],
			yaxis: 'y'
		};
	};
	return data_update
	};

// modify the plot data
async function replotData() {
	var data_update = dataUpdate(independent_axis_x);
	await Plotly.restyle(timeseries_plot,data_update);
};

// a function that returns a plotly layout update and data colour update
function axesUpdate(independent_axis_x) {
	let data_colour = axes_properties.map(prop => hex2plotlyRGB(prop.colour));
	let bg_colour = hex2plotlyRGB(figure_settings_values.background_colour);
	var data_update = {
		'marker.color': data_colour,
		'line.color': data_colour
	};
	if (independent_axis_x) {
		var iaxis = 'xaxis';
		var daxis = 'yaxis';
		var fixed_anchor = 'x';
		var fixed_overlay = 'y';
		var side_1 = 'left';
		var side_2 = 'right';
	} else {
		var iaxis = 'yaxis';
		var daxis = 'xaxis';
		var fixed_anchor = 'y';
		var fixed_overlay = 'x';
		var side_1 = 'bottom';
		var side_2 = 'top';
	};

	// set the title and independent axis
	var layout_update = {plot_bgcolor: bg_colour};
	layout_update[iaxis] = {
		color: 'black',
		domain: [0.1, 0.9],
		showgrid: figure_settings_values.independent_axis_gridlines,
		gridwidth: 2,
		showline: true,
		automargin:true,
		autorange: figure_settings_values.independent_axis_reverse ? 'reversed' : true
	};

	// now update the dependent axes
	for (let i = 0; i < 4; i++) {
		switch (i+1) {
			case 1:
				var axis = daxis;
				var anchor = fixed_anchor;
				var position = 0;
				var side = side_1;
				var overlay = null;
				break;
			case 2:
				var axis = daxis+'2';
				var anchor = fixed_anchor;
				var position = 1;
				var side = side_2;
				var overlay = fixed_overlay;
				break;
			case 3:
				var axis = daxis+'3';
				var anchor = 'free';
				var position = 0.05;
				var side = side_1;
				var overlay = fixed_overlay;
				break;
			case 4:
				var axis = daxis+'4';
				var anchor = 'free';
				var position = 0.95;
				var side = side_2;
				var overlay = fixed_overlay;
				break;
		}
		layout_update[axis] = {
			anchor: anchor,
			overlaying: overlay,
			position: position,
			side: side,
			color: data_colour[i],
			showgrid: axes_properties[i].gridlines,
			gridwidth: 2,
			showline: true,
			automargin:true,
			autorange: axes_properties[i].reverse ? 'reversed' : true,
		};
	}

	return [data_update, layout_update]
}


// modify the plot properties
async function modifyAxesProperties() {
	[data_update, layout_update] = axesUpdate(independent_axis_x);
	await Plotly.update(timeseries_plot,data_update,layout_update);
}

// function to get the current label values
function getLabels(independent_axis_x) {
	let layout = timeseries_plot.layout;
	var dependent_labels = [];
	if (independent_axis_x) {
		var independent_label = layout.xaxis.title;
		dependent_labels[0] = layout.yaxis.title;
		dependent_labels[1] = layout.yaxis2.title;
		dependent_labels[2] = layout.yaxis3.title;
		dependent_labels[3] = layout.yaxis4.title;
	} else {
		var independent_label = layout.yaxis.title;
		dependent_labels[0] = layout.xaxis.title;
		dependent_labels[1] = layout.xaxis2.title;
		dependent_labels[2] = layout.xaxis3.title;
		dependent_labels[3] = layout.xaxis4.title;
	};
	return [independent_label, dependent_labels]
};

// function to modify the labels
async function setLabels(independent_axis_x,independent_label,dependent_labels) {
	if (independent_axis_x) {
		var layout_update = {
			'xaxis.title': independent_label,
			'yaxis.title': dependent_labels[0],
			'yaxis2.title': dependent_labels[1],
			'yaxis3.title': dependent_labels[2],
			'yaxis4.title': dependent_labels[3]
		};
	} else {
		var layout_update = {
			'yaxis.title': independent_label,
			'xaxis.title': dependent_labels[0],
			'xaxis2.title': dependent_labels[1],
			'xaxis3.title': dependent_labels[2],
			'xaxis4.title': dependent_labels[3]
		};
	};
	await Plotly.relayout(timeseries_plot,layout_update);
};

// function to reposition the legend
async function repositionLegend(independent_axis_x) {
		if (independent_axis_x) {
			var legend = {x: 0.1, y: 1, xanchor: 'left', yanchor: 'top', bgcolor: 'rgba(255,255,255,0.5)'}
		} else {
			var legend = {x: 0, y: 0.9, xanchor: 'left', yanchor: 'top', bgcolor: 'rgba(255,255,255,0.5)'}
		};
		await Plotly.relayout(timeseries_plot,{legend: legend});
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
	let [independent_label, dependent_labels] = getLabels(independent_axis_x);
	updateFigureSettings()
	updateAxesProperties()
	modifyAxesProperties()
	.then(() => setLabels(independent_axis_x,independent_label,dependent_labels));
};

// function called when "Switch Axes" Button is clicked
function switchAxes() {
	let [independent_label, dependent_labels] = getLabels(independent_axis_x);
	independent_axis_x = !independent_axis_x;
	replotData()
	.then(() => modifyAxesProperties())
	.then(() => setLabels(independent_axis_x,independent_label,dependent_labels))
	.then(() => repositionLegend(independent_axis_x));
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
