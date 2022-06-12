<!DOCTYPE html>
<html lang='en'>
<meta charset="utf-8">
<title>SUNRISE Ship Servers</title>
<script src="/js/jquery-3.6.0.min.js"></script>
<script src="/js/d3.min.js"></script>
<script src="/js/plotly-2.12.1.min.js"></script>
<style>
</style>
</head>
<body>
<div id="temp"></div>
<div id="free"></div>
<script>
$.getJSON("monitorData.php", function(data) {
	var temp = [];
	var free = [];
	$.each(data, function(host, times) {
		var T = {name: host, mode: "line", type: "scatter", x:[], y:[]};
		var F = {name: host, mode: "line", type: "scatter", x:[], y:[]};
		$.each(times, function(t, row) {
			tt = new Date(t * 1000);
			T.x.push(tt);
			F.x.push(tt);
			T.y.push(row[0]);
			F.y.push(row[1]);
		});
		temp.push(T);
		free.push(F);
	});

	temp.sort(function(a, b) {return a.name > b.name;})
	free.sort(function(a, b) {return a.name > b.name;})
	console.log(temp);

	var config = {responsive: true};
	
	Plotly.newPlot("temp", temp, {
			title: {text: "Temperature"},
                	yaxis: {title: "Centigrade"},
			autosize: true,
		}, config);
	Plotly.newPlot("free", free, {
			title: {text: "Free Space"},
			yaxis: {title: "Gigabytes"},
			autosize: true,
		}, config);
});

</script>
</body>
</html>
