<?php
// Load recent data from the flow through sensors
header('Content-Type: application/json');
header('Cache-Control: no-cache');
header('X-Accel-Buffering: no');

$nback = array_key_exists("nback", $_GET) ? $_GET["nback"] : 2; # Number of days into the past
$names = array_key_exists("vars", $_GET) ? $_GET["vars"] : "temp"; # Variables to fetch
$dbname = "sunrise";

$sql = "SELECT t,$names FROM met WHERE t>(CURRENT_TIMESTAMP - $nback) ORDER BY t LIMIT 10000;";

$conn = pg_connect("dbname=$dbname");
if (!$conn) {
	exit(json_encode(array("error" => "unable to open database $dbname")));
}

$result = pg_query($conn, $sql);

if (!$result) {
	exit(json_encode(array("error" => "Executing query $sql")));
}

$info = array();

while ($row = pg_fetch_row($result)) {
	print_r($row);
	$info[$row[0]][round($row[1])] = [$row[2], $row[3]];
}

echo(json_encode($info));
?>
