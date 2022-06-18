<?php

header('Content-Type: application/json');
header('Cache-Control: no-cache');
header('X-Accel-Buffering: no');

// get json from fetch
$input = file_get_contents('php://input');

// decode the passed data
$passData = json_decode($input,true);

// define an output
$output = array(
  'PE_x_data' => [],
  'PS_x_data' => [],
  'PE_y_data' => [],
  'PS_y_data' => [],
  'PE_c_data' => [],
  'PS_c_data' => []
);

// map input variables to database variables
$variables = array(
  'None' => '',
  'Time' => 't',
  'Inertial Periods' => '',
  'Latitude' => 'lat',
  'Longitude' => 'lon',
  'Salinity' => 'sp',
  'Temperature' => 'temp',
  'U - Slab Model' => '',
  'V - Slab Model' => ''
);

$pe_variables = implode(',',array(
  $variables[$passData['x_variable']],
  $variables[$passData['y_variable']],
  $variables[$passData['data_PE']]
));

$ps_variables = implode(',',array(
  $variables[$passData['x_variable']],
  $variables[$passData['y_variable']],
  $variables[$passData['data_PS']]
));

// access the database
$dbname = "sunrise";

$sql = "SELECT $1 FROM met";
$sql.= " WHERE ship=$2";
$sql.= " AND t BETWEEN $3 AND $4";
$sql.= " ORDER BY t LIMIT 10000;";

try {
  $conn = pg_connect("dbname=$dbname");
  if (!$conn) {
    exit(json_encode(array("error" => "unable to open database $dbname")));
  }

  $pe_result = pg_query_params($conn, $sql, array($pe_variables,'pe',$passData['start_time'],$passData['end_time']));
  if (!$pe_result) {
    exit(json_encode(array("error" => "Executing $sql")));
  }

  $output = pg_fetch_all($pe_result);
} catch (Exception $e) {
  exit(json_encode(array("error" => $e->getMessage())));
}

// echo the output
echo json_encode($output);

?>
