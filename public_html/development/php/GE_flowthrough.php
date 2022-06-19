<?php
// Flowthrough from database

header("Content-Type: application/xml");
header('Cache-Control: no-cache');
header('X-Accel-Buffering: no');

// Set up SQL query

$nback = 48; # number of hours to search back

$variables = "t,"; # time
$variables .= "ROUND(lon::numeric,4),"; # longitude
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

    $pe_data = pg_fetch_all($pe_result,PGSQL_NUM);
    $ps_data = pg_fetch_all($ps_result,PGSQL_NUM);
} catch (Exception $e) {
	exit(json_encode(array("error" => $e->getMessage())));
}

// test whether we have data
// echo(json_encode($pe_data));
// echo("\n\n");

// spit out KML via the XMLWriter

$r = new XMLWriter();
$r->openMemory(); // Build in memory
$r->setIndent(true);
$r->startDocument("1.0", "UTF-8"); // XML type
$r->startElement("kml"); // Start a kml stanza
$r->writeAttribute("xmlns", "http://www.opengis.net/kml/2.2");
$r->startElement("Document");
$r->writeElement("name", "Flowthrough");

$r->startElement("Style");
$r->writeAttribute("id","sunrise_lines");
$r->startElement("LineStyle");
$r->writeElement("width",5);
$r->endElement(); // Linestyle
$r->startElement("BalloonStyle");
$r->startElement("text");
$text_string = "$[sunriseData/Time/displayName] $[sunriseData/Time]<br/>";
$text_string .= "$[sunriseData/lon/displayName] $[sunriseData/lon]<br/>";
$text_string .= "$[sunriseData/lat/displayName] $[sunriseData/lat]<br/>";
$text_string .= "$[sunriseData/temp/displayName] $[sunriseData/temp]<br/>";
$text_string .= "$[sunriseData/sal/displayName] $[sunriseData/sal]";
$r->writeCData($text_string);
$r->endElement(); // text
$r->endElement(); // BalloonStyle
$r->endElement(); // Style

$r->startElement("Schema");
$r->writeAttribute("name","sunriseData");
$r->writeAttribute("id","sunriseData");
$r->startElement("SimpleField");
$r->writeAttribute("type","string");
$r->writeAttribute("name","Time");
$r->startElement("displayName");
$r->writeCData("<b>Time</b>");
$r->endElement(); // displayName;
$r->endElement(); // SimpleField - time
$r->startElement("SimpleField");
$r->writeAttribute("type","float");
$r->writeAttribute("name","lon");
$r->startElement("displayName");
$r->writeCData("<b>Longitude</b>");
$r->endElement();
$r->endElement(); // SimpleField - lon
$r->startElement("SimpleField");
$r->writeAttribute("type","float");
$r->writeAttribute("name","lat");
$r->startElement("displayName");
$r->writeCData("<b>Latitude</b>");
$r->endElement();
$r->endElement(); // SimpleField - lat
$r->startElement("SimpleField");
$r->writeAttribute("type","float");
$r->writeAttribute("name","temp");
$r->startElement("displayName");
$r->writeCData("<b>Temperature</b>");
$r->endElement();
$r->endElement(); // SimpleField - temp
$r->startElement("SimpleField");
$r->writeAttribute("type","float");
$r->writeAttribute("name","sal");
$r->startElement("displayName");
$r->writeCData("<b>Salinity</b>");
$r->endElement();
$r->endElement(); // SimpleField - sal
$r->endElement(); // Schema

$r->startElement("Folder"); // Pelican salinity folder
$r->writeAttribute("id","PE_salinity");
$r->writeElement("name","PE Salinity");

$start_time = $pe_data[0][0];
$start_lon = $pe_data[0][1];
$start_lat = $pe_data[0][2];
foreach (range(1, count($pe_data)-1) as $ii) {
	$end_time = $pe_data[$ii][0];
	$end_lon = $pe_data[$ii][1];
	$end_lat = $pe_data[$ii][2];
	$end_temp = $pe_data[$ii][3];
	$end_sal = $pe_data[$ii][4];
	
	$r->startElement("Placemark");

	$r->startElement("TimeSpan");
	$r->writeElement("begin",str_replace(' ','T',$start_time).":00");
	$r->writeElement("end",str_replace(' ','T',$end_time).":00");
	$r->endElement(); // TimeSpan
	$r->startElement("LineString");
	$r->writeElement("coordinates","$start_lon,$start_lat $end_lon,$end_lat");
	$r->endElement(); // Linestring


	$r->writeElement("styleUrl","#sunrise_lines");
	$r->startElement("Style");
	$r->startElement("LineStyle");
	$r->writeElement("color","ff000000");
	$r->endElement(); // LineStyle
	$r->endElement(); // Style
	
	$r->startElement("ExtendedData");
	$r->startElement("SchemaData");
	$r->writeAttribute("schemaUrl","#sunriseData");
	$r->startElement("SimpleData");
	$r->writeAttribute("name","Time");
	$r->text(substr($end_time,0,16));
	$r->endElement(); // SimpleData - Time
	$r->startElement("SimpleData");
	$r->writeAttribute("name","lon");
	$r->text($end_lon);
	$r->endElement(); // SimpleData - lon
	$r->startElement("SimpleData");
	$r->writeAttribute("name","lat");
	$r->text($end_lat);
	$r->endElement(); // SimpleData - lat
	$r->startElement("SimpleData");
	$r->writeAttribute("name","temp");
	$r->text($end_temp);
	$r->endElement(); // SimpleData - temp
	$r->startElement("SimpleData");
	$r->writeAttribute("name","sal");
	$r->text($end_sal);
	$r->endElement(); // SimpleData - sal
	$r->endElement(); // SchemaData 
	$r->endElement(); // ExtendedData
	
	$r->endElement(); // Placemark

	$start_time = $end_time;
	$start_lon = $end_lon;
	$start_lat = $end_lat;	
}

$r->endElement(); // Pelican salinity folder

$r->endElement(); // Document
$r->endElement(); // kml
$r->endDocument(); // XML
echo $r->outputMemory(true); // Clean up and generate a string
?>
