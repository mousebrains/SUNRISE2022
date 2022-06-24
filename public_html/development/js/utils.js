function datetime2str(dt) {
	var parts = dt.toISOString().split(":")
	return (parts[0]+':'+parts[1])
};

function parseDateString(ds) {
	// all datestrings are UTC with form YYYY-MM-DDTHH:mm
	return new Date(ds+':00+00:00')
};

function hex2plotlyRGB(hex) {
	var result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
	var r = parseInt(result[1], 16);
	var g = parseInt(result[2], 16);
	var b = parseInt(result[3], 16);
 	return 'rgb(' + r + ',' + g + ',' + b + ')'
}

function setCookie(cname, cvalue) {
  let expires = "max-age="+ 60*60*24*28;
  document.cookie = (cname + "=" + cvalue + "; " + expires + "; path=/");
}

function getCookies() {
  let cookie = document.cookie;
	console.log(cookie)
  let cookie_strings = cookie.split(';');
	console.log(cookie_strings)
	let cookies = cookie_strings.map(co => co.split('='))
	return cookies
}

// ** DEFINE NEW MIN AND MAX FUNCTIONS TO HANDLE NULL VALUES

const my_min = (values) => values.reduce((m, v) => (v != null && v < m ? v : m), Infinity);
const my_max = (values) => values.reduce((m, v) => (v != null && v > m ? v : m), -Infinity);
