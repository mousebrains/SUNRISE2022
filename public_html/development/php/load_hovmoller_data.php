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
  'None' => 'NULL',
  'Time' => 't',
  'Inertial Periods' => 'ROUND(CAST(((DATE_PART('day', t::timestamp - '2022-06-17 12:00:00'::timestamp) * 24 + DATE_PART('hour', t::timestamp - '2022-06-17 12:00:00'::timestamp)) * 60 + DATE_PART('minute', t::timestamp - '2022-06-17 12:00:00'::timestamp))/1497 as NUMERIC),2)';
  'Latitude' => 'lat',
  'Longitude' => 'lon',
  'Salinity' => 'sp',
  'Temperature' => 'temp',
  'U - Slab Model' => 'NULL',
  'V - Slab Model' => 'NULL'
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
//$pe_sql.= " AND mod(minute(t),$3) = 0";
$pe_sql.= " AND (EXTRACT(MINUTE FROM t) % $3) = 0";
$pe_sql.= " ORDER BY t LIMIT 10000;";

$ps_sql = "SELECT $ps_variables FROM met";
$ps_sql.= " WHERE ship='ps'";
$ps_sql.= " AND t BETWEEN $1 AND $2";
//$ps_sql.= " AND mod(minute(t),$3) = 0";
$ps_sql.= " AND (EXTRACT(MINUTE FROM t) % $3) = 0";
$ps_sql.= " ORDER BY t LIMIT 10000;";

try {
  $conn = pg_connect("dbname=$dbname");
  if (!$conn) {
    exit(json_encode(array("error" => "unable to open database $dbname")));
  }

  if (strcmp($passData['data_PE'],'None') !== 0) {
    $pe_result = pg_query_params($conn, $pe_sql, array($passData['start_time'],$passData['end_time'],$passData['time_resolution']));
    if (!$pe_result) {
      exit(json_encode(array("error" => "Executing $pe_sql")));
    }
    $pe_data = pg_fetch_all($pe_result,PGSQL_NUM);
    $output['PE_x_data'] = array_column($pe_data,0);
    $output['PE_y_data'] = array_column($pe_data,1);
    $output['PE_c_data'] = array_column($pe_data,2);
  }

  if (strcmp($passData['data_PS'],'None') !== 0) {
    $ps_result = pg_query_params($conn, $ps_sql, array($passData['start_time'],$passData['end_time'],$passData['time_resolution']));
    if (!$ps_result) {
      exit(json_encode(array("error" => "Executing $ps_sql")));
    }
    $ps_data = pg_fetch_all($ps_result,PGSQL_NUM);
    $output['PS_x_data'] = array_column($ps_data,0);
    $output['PS_y_data'] = array_column($ps_data,1);
    $output['PS_c_data'] = array_column($ps_data,2);
  }



} catch (Exception $e) {
  exit(json_encode(array("error" => $e->getMessage())));
}

// echo output
echo json_encode($output);

?>
