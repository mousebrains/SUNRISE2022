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
<h1>SUNRISE2022 Github</h1>
<ul>
<?php
$skip = array(".", "..", ".git", ".gitignore");
$files = scandir("."); # All files in this directory
natcasesort($files); # Case insensitive natural order sorting
foreach($files as $item) {
	if (!in_array($item, $skip) and is_dir($item)) {
		echo "<li><a href='$item'>$item</a></li>\n";
	}
}
?>
</ul>
</body>
</html>
