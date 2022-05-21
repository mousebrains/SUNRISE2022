<?php

header('Content-Type: application/json');

// get json from fetch
$input = file_get_contents('php://input');

// decode the passed data
$passData = json_decode($input);

// define an output
$output = array(
  'Pelican_independent_values' => $passData['independent_variable'],
  'PointSur_independent_values' => $passData['independent_variable'],
  'data_1_values' => $passData['data_1'],
  'data_2_values' => [1,2,3,4],
  'data_3_values' => [],
  'data_4_values' => $passData['start_time']
);

// echo the output
echo json_encode($output);

?>
