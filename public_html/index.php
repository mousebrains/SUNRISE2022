<!DOCTYPE html>
<html lang='en'>
<head>
  <meta charset="utf-8">
  <title>SUNRISE 2022</title>
  <link rel="apple-touch-icon" sizes="180x180" href="favicons/apple-touch-icon.png">
  <link rel="icon" type="image/png" sizes="32x32" href="favicons/favicon-32x32.png">
  <link rel="icon" type="image/png" sizes="16x16" href="favicons/favicon-16x16.png">
  <link rel="icon" sizes="any" href="favicon.ico">
  <link rel="manifest" href="favicons/site.webmanifest">
</head>
<body>
<h1>SUNRISE 2022</h1>
<ul>
<?php
$skip = array(".", "..", "css", "favicons", "images", "js");
$files = scandir("."); # All files in this directory
natcasesort($files); # Case insensitive natural order sorting
foreach($files as $item) {
	if (!in_array($item, $skip) and is_dir($item)) {
		echo "<li><a href='$item'>$item</a></li>\n";
	}
}
$host = gethostname();
echo "<li><a href='";
if ($host and strlen($host) > 1 and (substr($host, 0, 2) == "ps")) {
	echo "https://192.168.1.162/";
} else {
	echo "https://coriolix.ceoas.oregonstate.edu/ptsur/sensor/flowthrough/plots/";
}
echo "'>Point Sur flow through data</li>\n";
?>
<li><a href=logViewer.php>log files</a></li>
<li><a href=https://sunrise.ceoas.oregonstate.edu/monitor.php>System monitor</a></li>
</ul>
</body>
</html>
