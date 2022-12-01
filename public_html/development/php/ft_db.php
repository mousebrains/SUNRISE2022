<?php
// Load recent data from the flow through sensors
header('Content-Type: application/json');
header('Cache-Control: no-cache');
header('X-Accel-Buffering: no');

$nback = array_key_exists("nback", $_GET) ? $_GET["nback"] : 60; # Number of minutes into the past
$ship = array_key_exists("ship", $_GET) ? $_GET["ship"] : "pe"; # Name of ship
$names = array_key_exists("vars", $_GET) ? $_GET["vars"] : "temp"; # Variables to fetch

$names = "ROUND(temp::numeric,4),";
$names .= " ROUND(EXTRACT(epoch FROM t - '2022-06-17 12:00:00+00')/89820::numeric,4),";
$names .= " ROUND(sp::numeric,4)"; # Trying to get temp,inertial periods,salinity

$dbname = "sunrise";

$sql = "SELECT t,$names FROM met";
$sql.= " WHERE ship=$1";
$sql.= " AND t>=(CURRENT_TIMESTAMP - make_interval(0,0,0,0,0,$2))";
$sql.= " ORDER BY t LIMIT 10000;";

try {
    $conn = pg_connect("dbname=$dbname");
    if (!$conn) {
	exit(json_encode(array("error" => "unable to open database $dbname")));
    }

    $result = pg_query_params($conn, $sql, array($ship, $nback));
    if (!$result) {
	exit(json_encode(array("error" => "Executing $sql")));
    }

    echo(json_encode(pg_fetch_all($result,PGSQL_NUM)));
} catch (Exception $e) {
	exit(json_encode(array("error" => $e->getMessage())));
}
?>
