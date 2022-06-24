<?php
// Flowthrough from database

header("Content-Type: application/xml");
header('Cache-Control: no-cache');
header('X-Accel-Buffering: no');

// Define cmaps

const SALINITY_CMAP = array(
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

const TEMPERATURE_CMAP = array(
  '#ffa4fefc','#ff9dfcf9','#ff95faf6','#ff8df7f4','#ff85f4f2','#ff7df2f1','#ff74eef1','#ff6cebf1',
  '#ff64e8f1','#ff5de4f2','#ff56e0f3','#ff4fdcf4','#ff48d9f5','#ff42d5f6','#ff3cd1f7','#ff37cdf8',
  '#ff31c9f8','#ff2cc5f9','#ff28c1fa','#ff23bdfa','#ff1eb9fb','#ff1ab5fb','#ff16b1fb','#ff12aefb',
  '#ff0eaafb','#ff0ba6fb','#ff08a2fb','#ff079efb','#ff069bfb','#ff0697fa','#ff0693fa','#ff0890f9',
  '#ff098cf9','#ff0c88f8','#ff0e85f7','#ff1181f6','#ff147ef5','#ff167af4','#ff1977f3','#ff1c74f2',
  '#ff1e70f0','#ff216def','#ff236aed','#ff2667ec','#ff2864ea','#ff2b61e8','#ff2d5ee6','#ff305be5',
  '#ff3258e3','#ff3456e0','#ff3753de','#ff3950dc','#ff3b4eda','#ff3e4bd7','#ff4049d5','#ff4247d2',
  '#ff4445d0','#ff4742cd','#ff4940cb','#ff4b3ec8','#ff4d3dc5','#ff4f3bc2','#ff5139bf','#ff5337bd',
  '#ff5635b8','#ff5733b5','#ff5932b2','#ff5b31af','#ff5c2fac','#ff5e2ea9','#ff5f2ca6','#ff612ba3',
  '#ff622aa0','#ff63299c','#ff642899','#ff662696','#ff672593','#ff682490','#ff69238d','#ff692289',
  '#ff6a2186','#ff6b2083','#ff6b1f80','#ff6c1d7d','#ff6d1c7a','#ff6d1b76','#ff6d1a73','#ff6e1970',
  '#ff6e186d','#ff6e176a','#ff6e1566','#ff6e1463','#ff6e1360','#ff6e125d','#ff6d115a','#ff6d0f57',
  '#ff6d0e53','#ff6c0d50','#ff6b0c4d','#ff6a0b4a','#ff690a46','#ff680a43','#ff660940','#ff65093c',
  '#ff620939','#ff600935','#ff5d0932','#ff5a0a2e','#ff560a2b','#ff520b27','#ff4e0b24','#ff4a0c20',
  '#ff450c1d','#ff400b1a','#ff3b0b17','#ff360b14','#ff320a12','#ff2d090f','#ff28080d','#ff23070a',
  '#ff1f0608','#ff1b0406','#ff160304','#ff120203','#ff0e0102','#ff090101','#ff060000','#ff030000'
);

function salinity_colour($svalue) : string {
  try {
    $smin = 24.0;
    $smax = 32.0;
    // convert salinity to a float
    $svalue = (float)$svalue;

    // check salinity is in a reasonable range
    if ( $svalue <= 0 ) {
      throw new Exception('Salinity must be positive');
    }
    if ( $svalue > 40) {
      throw new Exception('Salinity too large');
    }

    // map points outside of range to the range limits
    if ( $svalue < $smin ) {
      $svalue = $smin;
    }
    if ( $svalue > $smax ) {
      $svalue = $smax;
    }

    // map salinity to index
    $index = (($svalue - $smin)/($smax - $smin)*127);

    return SALINITY_CMAP[(int)$index];
  }
  catch (exception $e) {
    // return transparent colour upon error
    return '#00000000';
  }
}

function temperature_colour($tvalue) : string {
  try {
    $tmin = 30.0;
    $tmax = 33.0;
    // convert temperature to a float
    $tvalue = (float)$tvalue;

    // check temperature is in a reasonable range
    if ( $tvalue <= 0 ) {
      throw new Exception('Temperature must be positive');
    }
    if ( $tvalue > 40) {
      throw new Exception('Temperature too large');
    }

    // map points outside of range to the range limits
    if ( $tvalue < $tmin ) {
      $tvalue = $tmin;
    }
    if ( $tvalue > $tmax ) {
      $tvalue = $tmax;
    }

    // map salinity to index
    $index = (1 - ($tvalue - $tmin)/($tmax - $tmin))*127;

    return TEMPERATURE_CMAP[(int)$index];
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
$sql.= " AND EXTRACT(SECOND FROM t) = 0";
$sql.= " ORDER BY t LIMIT 15000;";

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
$r->writeAttribute("id","pe_lines");
$r->startElement("LineStyle");
$r->writeElement("width",5);
$r->endElement(); // Linestyle
$r->startElement("BalloonStyle");
$r->startElement("text");
$text_string = "<b>RV Pelican</b><br/>";
$text_string .= "$[sunriseData/Time/displayName] $[sunriseData/Time]<br/>";
$text_string .= "$[sunriseData/lon/displayName] $[sunriseData/lon] &degE<br/>";
$text_string .= "$[sunriseData/lat/displayName] $[sunriseData/lat] &degN<br/>";
$text_string .= "$[sunriseData/temp/displayName] $[sunriseData/temp] &degC<br/>";
$text_string .= "$[sunriseData/sal/displayName] $[sunriseData/sal] PSU";
$r->writeCData($text_string);
$r->endElement(); // text
$r->endElement(); // BalloonStyle
$r->endElement(); // Style

$r->startElement("Style");
$r->writeAttribute("id","ps_lines");
$r->startElement("LineStyle");
$r->writeElement("width",5);
$r->endElement(); // Linestyle
$r->startElement("BalloonStyle");
$r->startElement("text");
$text_string = "<b>RV Point Sur</b><br/>";
$text_string .= "$[sunriseData/Time/displayName] $[sunriseData/Time]<br/>";
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

// Pelican Salinity
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


	$r->writeElement("styleUrl","#pe_lines");
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

// Pelican Temperature
$r->startElement("Folder"); // Pelican temperature folder
$r->writeAttribute("id","PE_temperature");
$r->writeElement("name","PE Temperature");
$r->writeElement("visibility",0);

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
  $r->writeElement("visibility",0);

	$r->startElement("TimeSpan");
	$r->writeElement("begin",str_replace(' ','T',$start_time).":00");
	$r->writeElement("end",str_replace(' ','T',$end_time).":00");
	$r->endElement(); // TimeSpan
	$r->startElement("LineString");
	$r->writeElement("coordinates","$start_lon,$start_lat $end_lon,$end_lat");
	$r->endElement(); // Linestring


	$r->writeElement("styleUrl","#pe_lines");
	$r->startElement("Style");
	$r->startElement("LineStyle");
	$r->writeElement("color",temperature_colour($end_sal));
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

$r->endElement(); // Pelican temperature folder

// Point Sur Salinity
$r->startElement("Folder"); // Point Sur salinity folder
$r->writeAttribute("id","PS_salinity");
$r->writeElement("name","PS Salinity");

$start_time = $ps_data[0][0];
$start_lon = $ps_data[0][1];
$start_lat = $ps_data[0][2];
foreach (range(1, count($ps_data)-1) as $ii) {
	$end_time = $ps_data[$ii][0];
	$end_lon = $ps_data[$ii][1];
	$end_lat = $ps_data[$ii][2];
	$end_temp = $ps_data[$ii][3];
	$end_sal = $ps_data[$ii][4];

	$r->startElement("Placemark");

	$r->startElement("TimeSpan");
	$r->writeElement("begin",str_replace(' ','T',$start_time).":00");
	$r->writeElement("end",str_replace(' ','T',$end_time).":00");
	$r->endElement(); // TimeSpan
	$r->startElement("LineString");
	$r->writeElement("coordinates","$start_lon,$start_lat $end_lon,$end_lat");
	$r->endElement(); // Linestring


	$r->writeElement("styleUrl","#ps_lines");
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

$r->endElement(); // Point Sur salinity folder

// Point Sur Temperature
$r->startElement("Folder"); // Point Sur temperature folder
$r->writeAttribute("id","PS_temperature");
$r->writeElement("name","PS Temperature");
$r->writeElement("visibility",0);

$start_time = $ps_data[0][0];
$start_lon = $ps_data[0][1];
$start_lat = $ps_data[0][2];
foreach (range(1, count($ps_data)-1) as $ii) {
	$end_time = $ps_data[$ii][0];
	$end_lon = $ps_data[$ii][1];
	$end_lat = $ps_data[$ii][2];
	$end_temp = $ps_data[$ii][3];
	$end_sal = $ps_data[$ii][4];

	$r->startElement("Placemark");
  $r->writeElement("visibility",0);

	$r->startElement("TimeSpan");
	$r->writeElement("begin",str_replace(' ','T',$start_time).":00");
	$r->writeElement("end",str_replace(' ','T',$end_time).":00");
	$r->endElement(); // TimeSpan
	$r->startElement("LineString");
	$r->writeElement("coordinates","$start_lon,$start_lat $end_lon,$end_lat");
	$r->endElement(); // Linestring


	$r->writeElement("styleUrl","#ps_lines");
	$r->startElement("Style");
	$r->startElement("LineStyle");
	$r->writeElement("color",temperature_colour($end_sal));
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

$r->endElement(); // Point Sur temperature folder

$r->endElement(); // Document
$r->endElement(); // kml
$r->endDocument(); // XML
echo $r->outputMemory(true); // Clean up and generate a string
?>
