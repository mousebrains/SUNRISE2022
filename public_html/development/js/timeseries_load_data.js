// define some constants
const MAX_NUMBER_DATAPOINTS = 10000; // maximum number of datapoints that can be loaded
const CRUISE_START_TIME = new Date("2020-06-25 17:00"); // cannot load data from before the start of the cruise

// function called when "Load Data Clicked"
function loadData () {
  // get values from the UI
  updateSetData()
  updateSetTime()
  // copy values of set_data_values and set_time_values into a single object
  // this also guards against changes in their value
  const passData = Object.assign({},set_data_values,set_time_values);
  // check the independent variable is set
  if (passData.independent_variable == 'None') {window.alert("Independent variable required"); return};
  // check the number of datapoints requested is valid
  let Ndatapoints = computeNumberDatapoints(passData);
  if (!validateNumberDatapoints(Ndatapoints)) {return};

  // request the data and modify plot
  requestData(passData)
  .then(data => updateDatasets(passData,data))
  .then(() => replotData())
  .then(() => {
    let independent_label = LABELS[passData.independent_variable] || '';
    setLabels(independent_axis_x,
              independent_label,
              datasets.map(ds => LABELS[ds.name.substring(3)]))
  })
  .catch(error => console.log(error))
};

//  .catch(error => window.alert("Loading Data Failed"));

// assign data to datasets
function updateDatasets(passData,data) {
  datasets[0].name = (passData.data_1 != 'None' ? passData.data_1 : '');
  datasets[1].name = (passData.data_2 != 'None' ? passData.data_2 : '');
  datasets[2].name = (passData.data_3 != 'None' ? passData.data_3 : '');
  datasets[3].name = (passData.data_4 != 'None' ? passData.data_4 : '');
  datasets[0].dependent = data.data_values_1
  datasets[1].dependent = data.data_values_2
  datasets[2].dependent = data.data_values_3
  datasets[3].dependent = data.data_values_4
  for (let i = 0; i < 4; i++) {
    switch (datasets[i].name.substring(0,2)) {
      case 'PE':
        datasets[i].independent = data.Pelican_independent_values; break;
      case 'PS':
        datasets[i].independent = data.PointSur_independent_values; break;
      default:
        datasets[i].independent = [];
    };
  };
};


async function requestData (passData) {
  const response = await fetch('./php/load_timeseries_data.php', {
    method: 'POST',
    mode: 'cors',
    headers: {
      'Content-Type': 'application/json',
      'Accept': 'application/json',
    },
    body: JSON.stringify(passData)
  });
  // return response.json();
  let data = await response.json();
  console.log(data);
  return generateData(passData)
}

async function dummyData (passData) {
  await new Promise(r => setTimeout(r, 1000));
  return generateData(passData)
}

function computeNumberDatapoints(passData) {
  // compute how many datapoints have been requested
  // this will return a negative number if start_time is after end_time
  // first determine how many variables we are loading
  var include_Pelican_independent = false;
  var include_PointSur_independent = false;
  var number_of_variables = 0;
  let data_variables = [passData.data_1,passData.data_2,passData.data_3,passData.data_4];
  data_variables.forEach((variable) => {
    switch (variable.substring(0,2)) {
      case 'PE':
        number_of_variables++;
        include_Pelican_independent = true;
        break;
      case 'PS':
        number_of_variables++;
        include_PointSur_independent = true;
        break;
    }
  });
  number_of_variables += include_Pelican_independent + include_PointSur_independent;
  console.log("number_of_variables = " + number_of_variables)

  //now determine the time span
  var start_time = parseDateString(passData.start_time);
  start_time = start_time > CRUISE_START_TIME ? start_time : CRUISE_START_TIME;
  var end_time = parseDateString(passData.end_time);
  let now = new Date();
  end_time = end_time < now ? end_time : now;
  let timespan = end_time - start_time; // in milliseconds

  // get number of datapoints at 1 per minute
  let number_of_datapoints = number_of_variables*parseInt(timespan/60000/passData.time_resolution)

  return number_of_datapoints
}

function validateNumberDatapoints(Ndatapoints) {
  if (Ndatapoints < 0) {window.alert("Start time before end time"); return false};
  if (Ndatapoints == 0) {
    window.alert("No data requested");
    return false
  }
  if (Ndatapoints > MAX_NUMBER_DATAPOINTS) {
    window.alert(Ndatapoints + " datapoints requested\n" +
                "Maximum is " + MAX_NUMBER_DATAPOINTS);
    return false
  }
  return true
}

function generateData(passData) {
  var data = {"Pelican_independent_values":["2020-06-25 17:00","2020-06-25 17:01","2020-06-25 17:02","2020-06-25 17:03","2020-06-25 17:04","2020-06-25 17:05","2020-06-25 17:06","2020-06-25 17:07","2020-06-25 17:08"],
          "PointSur_independent_values":["2020-06-25 17:06","2020-06-25 17:07","2020-06-25 17:08","2020-06-25 17:09","2020-06-25 17:10","2020-06-25 17:11"]}
  switch (passData.data_1.substring(0,2)) {
    case 'PE':
      data.data_values_1 = Array.from({length: 9}, () => (Math.random() * 10)); break;
    case 'PS':
      data.data_values_1 = Array.from({length: 9}, () => (Math.random() * 12 - 2)); break;
    default:
      data.data_values_1 = [];
  }
  switch (passData.data_2.substring(0,2)) {
    case 'PE':
      data.data_values_2 = Array.from({length: 9}, () => (Math.random() * 10)); break;
    case 'PS':
      data.data_values_2 = Array.from({length: 9}, () => (Math.random() * 12 - 2)); break;
    default:
      data.data_values_2 = [];
  }
  switch (passData.data_3.substring(0,2)) {
    case 'PE':
      data.data_values_3 = Array.from({length: 9}, () => (Math.random() * 10)); break;
    case 'PS':
      data.data_values_3 = Array.from({length: 9}, () => (Math.random() * 12 - 2)); break;
    default:
      data.data_values_3 = [];
  }
  switch (passData.data_4.substring(0,2)) {
    case 'PE':
      data.data_values_4 = Array.from({length: 9}, () => (Math.random() * 10)); break;
    case 'PS':
      data.data_values_4 = Array.from({length: 9}, () => (Math.random() * 12 - 2)); break;
    default:
      data.data_values_4 = [];
  }
  return data;
}
