<?php
// Flowthrough from database

header("Content-Type: application/xml");
header('Cache-Control: no-cache');
header('X-Accel-Buffering: no');

/////////////////////////////////////////
// some database magic courtesy of Pat //
/////////////////////////////////////////

$nback = 48;
$names = "lon,lat,temp,sp";
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

    $pe_result = pg_query_params($conn, $sql, array('pe', $nback));
    if (!$pe_result) {
	exit(json_encode(array("error" => "Executing $sql")));
    }

    $ps_result = pg_query_params($conn, $sql, array('ps', $nback));
    if (!$ps_result) {
	exit(json_encode(array("error" => "Executing $sql")));
    }

    echo(json_encode(pg_fetch_all($pe_result)));
} catch (Exception $e) {
	exit(json_encode(array("error" => $e->getMessage())));
}

// spit out KML via the XMLWriter

// $r = new XMLWriter();
// $r->openMemory(); // Build in memory
// $r->startDocument("1.0", "UTF-8"); // XML type
// $r->startElement("kml"); // Start a kml stanza
// $r->writeAttribute("xmlns", "http://www.opengis.net/kml/2.2");
// $r->startElement("Document");
// $r->writeElement("name", "Flowthrough");
//
// //$r->startElement("") //
//
// $r->endElement(); // Document
// $r->endElement(); // kml
// $r->endDocument(); // XML
// echo $r->outputMemory(true); // Clean up and generate a string
?>
