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

$pe_sql = "SELECT $pe_variables FROM met";
$pe_sql.= " WHERE ship='pe'";
$pe_sql.= " AND t BETWEEN $1 AND $2";
$pe_sql.= " ORDER BY t LIMIT 10000;";

$ps_sql = "SELECT $ps_variables FROM met";
$ps_sql.= " WHERE ship='ps'";
$ps_sql.= " AND t BETWEEN $1 AND $2";
$ps_sql.= " ORDER BY t LIMIT 10000;";

try {
  $conn = pg_connect("dbname=$dbname");
  if (!$conn) {
    exit(json_encode(array("error" => "unable to open database $dbname")));
  }

  $pe_result = pg_query_params($conn, $pe_sql, array($passData['start_time'],$passData['end_time']));
  if (!$pe_result) {
    exit(json_encode(array("error" => "Executing $pe_sql")));
  }

  $ps_result = pg_query_params($conn, $ps_sql, array($passData['start_time'],$passData['end_time']));
  if (!$ps_result) {
    exit(json_encode(array("error" => "Executing $ps_sql")));
  }

  $pe_data = pg_fetch_all($pe_result,PGSQL_NUM);
  $ps_data = pg_fetch_all($ps_result,PGSQL_NUM);
} catch (Exception $e) {
  exit(json_encode(array("error" => $e->getMessage())));
}

// echo the output
$output['PE_x_data'] = array_column($pe_data,0);
echo json_encode($output);

?>
