<?php
header('Content-Type: text/event-stream');
header('Cache-Control: no-cache');
header('X-Accel-Buffering: no');

$nback = array_key_exists("nback", $_GET) ? $_GET["nback"] : 2; # Number of days into the past

$sql = "SELECT host,t,ROUND((temp/1000)::NUMERIC, 1) AS temp, ROUND(free::NUMERIC,1) AS free";
$sql.= " FROM status";
$sql.= " WHERE t>=extract(EPOCH FROM (CURRENT_TIMESTAMP - INTERVAL '$nback days'))";
$sql.= " ORDER BY host,t;";

$conn = pg_connect("dbname=sunrise");
if (!$conn) {
	exit(json_encode(array("error" => "unable to open database")));
}

$result = pg_query($conn, $sql);
if (!$result) {
	exit(json_encode(array("error" => "Executing query")));
}

$info = array();
while ($row = pg_fetch_row($result)) {
	$info[$row[0]][round($row[1])] = [$row[2], $row[3]];
}
echo(json_encode($info));
?>
