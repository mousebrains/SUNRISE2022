<?php

header('Content-Type: application/json');

// get json from fetch
$input = file_get_contents('php://input');

// decode the passed data
$passData = json_decode($input,true);

// define an output
$output = array(
  'PE_x_data' => $passData['x_variable'],
  'PS_x_data' => $passData['x_variable'],
  'PE_y_data' => $passData['y_variable'],
  'PS_y_data' => $passData['y_variable'],
  'PE_c_data' => $passData['data_PE'],
  'PS_c_data' => $passData['data_PS']
);

// echo the output
echo json_encode($output);

?>
