<?php
// Flowthrough from database

header("Content-Type: application/xml");
header('Cache-Control: no-cache');
header('X-Accel-Buffering: no');

// Define cmaps

$salinity_cmap = array(
  '#ffd9ffff','#ffd6fefd','#ffd3fefc','#ffd1fdfb','#ffcefdfa','#ffccfcf9','#ffc9fcf8','#ffc7fbf7',
  '#ffc4fbf5','#ffc2fbf4','#ffbffaf3','#ffbdfaf2','#ffbaf9f1','#ffb8f9f0','#ffb5f8ef','#ffb3f8ee',
  '#ffb1f7ec','#ffb1f7ea','#ffb1f6e8','#ffb1f5e5','#ffb1f4e3','#ffb1f3e0','#ffb2f2de','#ffb2f1dc',
  '#ffb2f0d9','#ffb2efd7','#ffb2eed5','#ffb3edd2','#ffb3ecd0','#ffb3ebcd','#ffb3eacb','#ffb3e9c9',
  '#ffb4e8c6','#ffb4e7c1','#ffb4e5bd','#ffb5e3b8','#ffb5e1b4','#ffb6dfaf','#ffb6deab','#ffb7dca6',
  '#ffb7daa2','#ffb8d89d','#ffb8d799','#ffb8d594','#ffb9d390','#ffb9d18b','#ffbad087','#ffbace82',
  '#ffbbcc7e','#ffbbcb7a','#ffbcc976','#ffbcc872','#ffbdc66e','#ffbdc56a','#ffbec466','#ffbfc263',
  '#ffbfc15f','#ffc0bf5b','#ffc0be57','#ffc1bc53','#ffc1bb4f','#ffc2b94b','#ffc3b847','#ffc3b743',
  '#ffc3b43f','#ffc3b13d','#ffc3af3a','#ffc3ad38','#ffc2aa36','#ffc2a834','#ffc2a631','#ffc2a42f',
  '#ffc1a12d','#ffc19f2a','#ffc19d28','#ffc19a26','#ffc09824','#ffc09621','#ffc0931f','#ffc0911d',
  '#ffbe8e1d','#ffbd8b1d','#ffbb881d','#ffba841e','#ffb8811e','#ffb77e1e','#ffb57b1f','#ffb4781f',
  '#ffb2741f','#ffb17120','#ffaf6e20','#ffae6b20','#ffac6821','#ffab6421','#ffa96121','#ffa85e21',
  '#ffa65b22','#ffa55922','#ffa45622','#ffa35322','#ffa15122','#ffa04e23','#ff9f4b23','#ff9e4923',
  '#ff9c4623','#ff9b4323','#ff9a4124','#ff993e24','#ff973c24','#ff963924','#ff953624','#ff943424',
  '#ff903223','#ff8c3121','#ff882f1f','#ff852e1d','#ff812c1c','#ff7d2b1a','#ff792918','#ff762816',
  '#ff722714','#ff6e2512','#ff6a2411','#ff67220f','#ff63210d','#ff5f1f0b','#ff5b1e09','#ff581d08'
);

function salinity_colour($svalue) : string {
  try {
    $min = 24.0;
    $smax = 32.0;
    // convert salinity to a float
    $value = floatvar($svalue)

    // check salinity is in a reasonable range
    if ( $value <= 0 ) {
      throw new Exception('Salinity must be positive');
    }
    if ( $value > 40) {
      throw new Exception('Salinity too large');
    }

    // map points outside of range to the range limits
    if ( $value < $smin ) {
      $value = $smin;
    }
    if ( $value > $smax ) {
      $value = $smax;
    }

    // map salinity to index
    $index = (int)(($svalue - $smin)/($smax - $smin)*127);

    return $salinity_cmap($index);
  }
  catch (exception $e) {
    // return transparent colour upon error
    return '#00000000';
  }
}
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
$text_string .= "$[sunriseData/lon/displayName] $[sunriseData/lon] &degE<br/>";
$text_string .= "$[sunriseData/lat/displayName] $[sunriseData/lat] &degN<br/>";
$text_string .= "$[sunriseData/temp/displayName] $[sunriseData/temp] &degC<br/>";
$text_string .= "$[sunriseData/sal/displayName] $[sunriseData/sal] PSU";
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
	$r->writeElement("color",salinity_colour($end_sal));
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
