
// function called when "Load Data Clicked"
function loadData () {
  updateSetData()
  updateSetTime()
  // copy values of set_data_values and set_time_values into a single object
  // this also guards against changes in their value - I think
  const passData = Object.assign({},set_data_values,set_time_values);
  dummyData(passData)
  .then(data => updateDatasets(passData,data))
  .then(() => replotData())
  .then(() => {
    let independent_label = (passData.independent_variable != 'None' ? passData.independent_variable : '');
    setLabels(independent_axis_x,
              independent_label,
              datasets.map(ds => ds.name))
  });
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


// async function requestData (passData) {
//   const response = await fetch('./php/load_timeseries_data.php', {
//     method: 'POST',
//     headers: {
//       'Content-Type': 'application/json',
//       'Accept': 'application/json',
//     },
//     body: JSON.stringify(passData)
//   });
//   return response.json();
// }

async function dummyData (passData) {
  await new Promise(r => setTimeout(r, 2000));
  data = {"Pelican_independent_values":["2020-06-25 17:00","2020-06-25 17:01","2020-06-25 17:02","2020-06-25 17:03","2020-06-25 17:04","2020-06-25 17:05","2020-06-25 17:06","2020-06-25 17:07","2020-06-25 17:08"],
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
