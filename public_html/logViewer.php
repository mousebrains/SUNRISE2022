<!DOCTYPE html>
<html lang='en'>
<head>
<title>
SUNRISE 2022 Log Viewer
</title>
</head>
<body>
<?php
function tailFile(string $prefix, string $fn, int $nLines, bool $echoOutput=true) {
        if (($fp = @fopen($prefix . $fn, "r")) === false) {
                echo "$prefix . $fn not found\n";
                return;
        }
        fseek($fp, 0, SEEK_END);
        $chunkSize = $nLines * 100; // Guess at bytes we need to read backwards
        $cnt = 0;
        $output = "";
        $chunk = "";
        while (($cnt < $nLines) && (ftell($fp) > 0)) {
                $seek = min(ftell($fp), $chunkSize); // How far to seek backwards
                fseek($fp, -$seek, SEEK_CUR); // Seek backwards from where we're currently at
                $sPos = ftell($fp); // Starting position to seek back to
                $output = ($chunk = fread($fp, $seek)) . $output; // Prepend lines
                fseek($fp, $sPos); // Seek back to where we started
                $cnt += substr_count($chunk, "\n");
        }
        $output = substr($output, strpos($output, "\n")); // Strip off first partial line
        if ($echoOutput) {
                echo $output;
        }
        return $output;

}

$prefix = "/home/pat/logs/";

if (array_key_exists("fn", $_GET)) { // Display the tail of a file
        $n = array_key_exists("n", $_GET) ? $_GET["n"] : 200;
        $fn = $_GET["fn"];
        echo "<h1>$fn</h1>\n";
        echo "<pre>\n";
        tailFile($prefix, $fn, $n);
        echo "</pre>\n";
} else { // fn not in $_GET
        $n = strlen($prefix);
        echo "<h1>View server log files for the SUNRISE 2022 Cruise</h1>";
	echo "<ul>\n";
	$files = glob("$prefix*.log");
	natcasesort($files);
        foreach ($files as $fn) {
                $label = substr($fn, $n);
                echo "<li><a href='?fn=$label'>$label</a></li>\n";
        }
        echo "</ul>\n";
}
?>
</body>
</html>

