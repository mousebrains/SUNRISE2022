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

$output = $input;
$pe_variables = array(
  $variables["$input[x_variable]"],
  $variables["$input[y_variable]"],
  $variables["$input[data_PE]"]
);


//
//
//
// $ps_variables = array(
//   $variables[$input['x_variable']],
//   $variables[$input['y_variable']],
//   $variables[$input['data_PS']]
// );
//
// // access the database
// $dbname = "sunrise";
//
// $sql = "SELECT $1 FROM met";
// $sql.= " WHERE ship=$2";
// $sql.= " AND t BETWEEN $3 AND $4";
// $sql.= " ORDER BY t LIMIT 10000;";
//
// try {
//     $conn = pg_connect("dbname=$dbname");
//     if (!$conn) {
//       echo(json_encode(array("error" => "unable to open database $dbname")));
// 	exit(json_encode(array("error" => "unable to open database $dbname")));
//     }
//
//     $pe_result = pg_query_params($conn, $sql, array(implode(',',$pe_variables),'pe',$input['start_time'],$input['end_time']));
//     if (!$result) {
//       echo(json_encode(array("error" => "Executing $sql")));
// 	exit(json_encode(array("error" => "Executing $sql")));
//     }
//
//     echo(json_encode(pg_fetch_all($pe_result)));
// } catch (Exception $e) {
//   echo(json_encode(array("error" => $e->getMessage())));
// 	exit(json_encode(array("error" => $e->getMessage())));
// }

// echo the output
echo json_encode($output);

?>
