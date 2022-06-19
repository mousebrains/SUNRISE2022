<?php
// Flowthrough from database

header("Content-Type: application/xml");
header('Cache-Control: no-cache');
header('X-Accel-Buffering: no');

// Set up SQL query

$nback = 48; # number of hours to search back

$variables = "ROUND(lon::numeric,4),"; # longitude
$variables .= "ROUND(lat::numeric,4),"; # latitude
$variables .= "ROUND(temp::numeric,4),"; # temperature
$variables .= "ROUND(sp::numeric,4)"; # salinity

$dbname = "sunrise";

$sql = "SELECT $variables FROM met";
$sql.= " WHERE ship=$1";
$sql.= " AND t>=(CURRENT_TIMESTAMP - make_interval(0,0,0,0,$2,0))";
$sql.= " ORDER BY t LIMIT 10000;";

try {
    $conn = pg_connect("dbname=$dbname");
    if (!$conn) {
	exit(json_encode(array("error" => "unable to open database $dbname")));
    }

    $pe_result = pg_query_params($conn, $sql, array('pe', $nback));
    if (!$pe_result) {
	exit(json_encode(array("error" => "Executing $sql")));
    }

    $ps_result = pg_query_params($conn, $sql, array('ps', $nback));
    if (!$ps_result) {
	exit(json_encode(array("error" => "Executing $sql")));
    }

    echo(json_encode(pg_fetch_all($pe_result)));
    echo(json_encode(pg_fetch_all($ps_result)));
} catch (Exception $e) {
	exit(json_encode(array("error" => $e->getMessage())));
}

// spit out KML via the XMLWriter

$r = new XMLWriter();
$r->openMemory(); // Build in memory
$r->startDocument("1.0", "UTF-8"); // XML type
$r->startElement("kml"); // Start a kml stanza
$r->writeAttribute("xmlns", "http://www.opengis.net/kml/2.2");
$r->startElement("Document");
$r->writeElement("name", "Flowthrough");

//$r->startElement("") //

$r->endElement(); // Document
$r->endElement(); // kml
$r->endDocument(); // XML
echo $r->outputMemory(true); // Clean up and generate a string
?>
