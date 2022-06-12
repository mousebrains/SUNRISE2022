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
  // check the x and y variable is set
  if (passData.x_variable == 'None' || passData.y_variable == 'None') {
    window.alert("X and Y variables required");
    return
  };
  // check the number of datapoints requested is valid
  let Ndatapoints = computeNumberDatapoints(passData);
  if (!validateNumberDatapoints(Ndatapoints)) {return};

  //console.log(passData);

  // request the data and modify plot
  requestData(passData)
  .then(data => updateDatasets(passData,data))
  .then(() => replotData())
  .then(() => {
    let x_label = LABELS[passData.x_variable] || '';
    let y_label = LABELS[passData.y_variable] || '';
    setLabels(x_label,y_label)
  })
  .then(() => updateColourProperties())
  .then(() => setColourbar(passData.data_PE,passData.data_PS))
  .catch(error => console.log(error))
};

//  .catch(error => window.alert("Loading Data Failed"));

// assign data to datasets
function updateDatasets(passData,data) {
  dataset_PE.name = (passData.data_PE != 'None' ? passData.data_PE : '');
  dataset_PE.x_data = data.PE_x_data;
  dataset_PE.y_data = data.PE_y_data;
  dataset_PE.c_data = data.PE_c_data;
  dataset_PS.name = (passData.data_PS != 'None' ? passData.data_PS : '');
  dataset_PS.x_data = data.PS_x_data;
  dataset_PS.y_data = data.PS_y_data;
  dataset_PS.c_data = data.PS_c_data;
};


async function requestData (passData) {
  const response = await fetch('./php/load_hovmoller_data.php', {
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
  var include_Pelican = (passData.data_PE != 'None');
  var include_PointSur = (passData.data_PS != 'None');
  var number_of_variables = 3*(include_Pelican + include_PointSur);

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
  var data = {};
  switch (passData.x_variable) {
    case "Time":
      data["PE_x_data"] = ["2020-06-25 17:00","2020-06-25 17:01","2020-06-25 17:02","2020-06-25 17:03","2020-06-25 17:04","2020-06-25 17:05","2020-06-25 17:06","2020-06-25 17:07","2020-06-25 17:08"];
      data["PS_x_data"] = ["2020-06-25 17:00","2020-06-25 17:01","2020-06-25 17:02","2020-06-25 17:03","2020-06-25 17:04","2020-06-25 17:05","2020-06-25 17:06","2020-06-25 17:07","2020-06-25 17:08"];
      break;
    default:
      data["PE_x_data"] = Array.from({length: 9}, () => (Math.random()));
      data["PS_x_data"] = Array.from({length: 9}, () => (Math.random()));
  };

  switch (passData.y_variable) {
    case "Time":
      data["PE_y_data"] = ["2020-06-25 17:00","2020-06-25 17:01","2020-06-25 17:02","2020-06-25 17:03","2020-06-25 17:04","2020-06-25 17:05","2020-06-25 17:06","2020-06-25 17:07","2020-06-25 17:08"];
      data["PS_y_data"] = ["2020-06-25 17:00","2020-06-25 17:01","2020-06-25 17:02","2020-06-25 17:03","2020-06-25 17:04","2020-06-25 17:05","2020-06-25 17:06","2020-06-25 17:07","2020-06-25 17:08"];
      break;
    default:
      data["PE_y_data"] = Array.from({length: 9}, () => (Math.random()));
      data["PS_y_data"] = Array.from({length: 9}, () => (Math.random()));
  };

  switch (passData.data_PE) {
    case "None":
      data["PE_x_data"] = [];
      data["PE_y_data"] = [];
      data["PE_c_data"] = [];
      break;
    case "Time":
      data["PE_c_data"] = ["2020-06-25 17:00","2020-06-25 17:01","2020-06-25 17:02","2020-06-25 17:03","2020-06-25 17:04","2020-06-25 17:05","2020-06-25 17:06","2020-06-25 17:07","2020-06-25 17:08"];
      break;
    default:
      data["PE_c_data"] = Array.from({length: 9}, () => (Math.random() * 10))
  };

  switch (passData.data_PS) {
    case "None":
      data["PS_x_data"] = [];
      data["PS_y_data"] = [];
      data["PS_c_data"] = [];
      break;
    case "Time":
      data["PS_c_data"] = ["2020-06-25 17:00","2020-06-25 17:01","2020-06-25 17:02","2020-06-25 17:03","2020-06-25 17:04","2020-06-25 17:05","2020-06-25 17:06","2020-06-25 17:07","2020-06-25 17:08"];
      break;
    default:
      data["PS_c_data"] = Array.from({length: 9}, () => (Math.random() * 10))
  };
  return data;
}
