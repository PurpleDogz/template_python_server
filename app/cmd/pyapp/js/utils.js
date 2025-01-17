function get_tt_font_size() { return mobileCheck() ? "10px" : "12px"; }
function get_tt_font_title_size() { return mobileCheck() ? "12px" : "14px"; }
function get_tt_table_class() { return mobileCheck() ? "table table-hover table-dark table-sm1" : "table table-hover table-dark table-sm"; }

function resolveMousePoint(d0, d1, mouseDate, lessthan = true) {
	var dTarget = null;
	if (d0 == undefined && d1 != undefined) {
		dTarget = d1;
	} else if (d0 != undefined && d1 == undefined) {
		dTarget = d0;
	} else if (d0 != undefined && d1 != undefined) {
		if (lessthan) {
			dTarget = mouseDate - d0[0] < d1[0] - mouseDate ? d1 : d0;
		} else {
			dTarget = mouseDate - d0[0] > d1[0] - mouseDate ? d1 : d0;
		}
	}
	return dTarget;
}

function calcMouseOffset(id, event, offset, offset_flip) {
	let rect = document.querySelector(id).getBoundingClientRect();
	if (event.offsetX > (rect.width / 2)) {
		return offset_flip;
	}
	return offset
}

function createCookie(name, value, days) {
    var expires;

    if (days) {
        var date = new Date();
        date.setTime(date.getTime() + (days * 24 * 60 * 60 * 1000));
        expires = "; expires=" + date.toGMTString();
    } else {
        expires = "";
    }
    document.cookie = encodeURIComponent(name) + "=" + encodeURIComponent(value) + expires + "; path=/";
}

function readCookie(name) {
    var nameEQ = encodeURIComponent(name) + "=";
    var ca = document.cookie.split(';');
    for (var i = 0; i < ca.length; i++) {
        var c = ca[i];
        while (c.charAt(0) === ' ')
            c = c.substring(1, c.length);
        if (c.indexOf(nameEQ) === 0)
            return decodeURIComponent(c.substring(nameEQ.length, c.length));
    }
    return null;
}

function eraseCookie(name) {
    createCookie(name, "", -1);
}

function dateAdd(date, interval, units) {
	if(!(date instanceof Date))
	  return undefined;
	var ret = new Date(date); //don't change original date
	var checkRollover = function() { if(ret.getDate() != date.getDate()) ret.setDate(0);};
	switch(String(interval).toLowerCase()) {
	  case 'year'   :  ret.setFullYear(ret.getFullYear() + units); checkRollover();  break;
	  case 'quarter':  ret.setMonth(ret.getMonth() + 3*units); checkRollover();  break;
	  case 'month'  :  ret.setMonth(ret.getMonth() + units); checkRollover();  break;
	  case 'week'   :  ret.setDate(ret.getDate() + 7*units);  break;
	  case 'day'    :  ret.setDate(ret.getDate() + units);  break;
	  case 'hour'   :  ret.setTime(ret.getTime() + units*3600000);  break;
	  case 'minute' :  ret.setTime(ret.getTime() + units*60000);  break;
	  case 'second' :  ret.setTime(ret.getTime() + units*1000);  break;
	  default       :  ret = undefined;  break;
	}
	return ret;
 }

 function add_html_color(text, color, def_value=null, font_size=null) {
	if ( !text ) { return def_value; }
	var style = "color:" + color + ";";
	if ( font_size ) { style += "font-size:" + font_size + ";"; }
	return "<span style=\"" + style + "\">" + text + "</span>";
  }

  function secondsToDhms(seconds, disableSec = false) {
	seconds = Number(seconds);
	var d = Math.floor(seconds / (3600*24));
	var h = Math.floor(seconds % (3600*24) / 3600);
	var m = Math.floor(seconds % 3600 / 60);
	var s = Math.floor(seconds % 60);
	
	var dDisplay = d > 0 ? d + (d == 1 ? " day, " : " days, ") : "";
	var hDisplay = h > 0 ? h + (h == 1 ? " hr, " : " hr, ") : "";
	var mDisplay = m > 0 ? m + (m == 1 ? " min " : " min ") : "";
	var sDisplay = s > 0 ? "," + s + (s == 1 ? " sec" : " sec") : "";
	if ( disableSec ) { sDisplay = ""; }
	return dDisplay + hDisplay + mDisplay + sDisplay;
}

// Global Lookup for 7 element range
function get_scale_colors() {
	return get_powerscale_3();
}

// https://observablehq.com/@d3/color-schemes
// Muted
function get_powerscale_3() {
	const colors = d3[`scheme${'RdYlGn'}`][11];
	return [colors[9], colors[7], colors[4], colors[3], colors[2], colors[1], colors[0], colors[0]];
}

function get_intensity_color(i, factor = 1) {

	i = i / factor;

	if ( i < 70 ) { return  get_scale_colors()[0]; }
	if ( i < 75 ) { return  get_scale_colors()[1]; }
	if ( i < 80 ) { return  get_scale_colors()[2]; }
	if ( i < 85 ) { return  get_scale_colors()[3]; }
	if ( i < 90 ) { return  get_scale_colors()[4]; }
	return get_scale_colors()[5];
} 

function formatTime(date) {
	var d = new Date(date);
	return d.toLocaleTimeString();
}

function dateOnly2(date) {
	if ( date ) { return formatDate(moment(date)); }
	return "";
}

function addDays(numOfDays, date = new Date()) {
	var result = new Date(date);
	result.setDate(result.getDate() + numOfDays);
	return result;
}

function subtractDays(numOfDays, date = new Date()) {
	var result = new Date(date);
	result.setDate(result.getDate() - numOfDays);
	return result;
}

function formatDateShortTime(date) {
	if (moment(date).isSameOrAfter(moment(new Date()), 'day')) {
		return moment(date).format('[Today at ]h:mm a');
	}
	if (moment(date).isSame(moment(subtractDays(1)), 'day')) {
		return moment(date).format('[Yesterday at ]h:mm a');
	}
	return moment(date).format('Do MMMM YYYY [at] h:mm a');
}

function formatDatePlusTimeFromUTC(date) {
	var stillUtc = moment.utc(date).toDate();
	return moment(stillUtc).local().format('Do MMMM YYYY h:mm:ss a');
}

function formatDateFromUTC(date) {
	var stillUtc = moment.utc(date).toDate();
	return moment(stillUtc).local().format('Do MMMM YYYY');
}

function formatDate_US(date, separator = '/') {
	var d = new Date(date),
		month = '' + (d.getMonth() + 1),
		day = '' + d.getDate(),
		year = d.getFullYear();

	if (month.length < 2)
		month = '0' + month;
	if (day.length < 2)
		day = '0' + day;

	return [month, day, year].join(separator);
}

function formatDate(date, separator = '-') {
	var d = new Date(date),
		month = '' + (d.getMonth() + 1),
		day = '' + d.getDate(),
		year = d.getFullYear();

	if (month.length < 2)
		month = '0' + month;
	if (day.length < 2)
		day = '0' + day;

	return [year, month, day].join(separator);
}

function secondsToTime(s, truncateSeconds = false, addMilliseconds = false) {
	seconds = parseInt(s);
	var hours = Math.floor(seconds / 3600);
	var minutes = Math.floor((seconds - (hours * 3600)) / 60);
	var seconds = seconds - (hours * 3600) - (minutes * 60);
	var time = "";

	if (hours != 0) {
		time = hours + ":";
	}
	if (minutes != 0 || time !== "") {
		minutes = (minutes < 10 && time !== "") ? "0" + minutes : String(minutes);
		time += minutes;
	}


	if (time === "") {
		if ( addMilliseconds ) {
			var mseconds = Math.round(1000*(parseFloat(s) - seconds),0);
			if ( mseconds > 0 ) {
				var mseconds_str = String(mseconds);
				if ( mseconds < 10 ) { mseconds_str =  "00" + mseconds; }
				else if ( mseconds < 100 ) { mseconds_str =  "0" + mseconds; }
				seconds += "." + mseconds_str;
			}
		}	
		time = seconds + "s";
	} else {
		if (!truncateSeconds && seconds > 0) {
			time += ":";
			time += (seconds < 10) ? "0" + seconds : String(seconds);
		} else if (hours == 0) {
			time = "0:" + (time < 10 ? "0" + time : String(time));
		}
	}


	return time;
}

function mobileCheck() {
	let check = false;
	(function(a) {
		if (/(android|bb\d+|meego).+mobile|avantgo|bada\/|blackberry|blazer|compal|elaine|fennec|hiptop|iemobile|ip(hone|od)|iris|kindle|lge |maemo|midp|mmp|mobile.+firefox|netfront|opera m(ob|in)i|palm( os)?|phone|p(ixi|re)\/|plucker|pocket|psp|series(4|6)0|symbian|treo|up\.(browser|link)|vodafone|wap|windows ce|xda|xiino/i.test(a) || /1207|6310|6590|3gso|4thp|50[1-6]i|770s|802s|a wa|abac|ac(er|oo|s\-)|ai(ko|rn)|al(av|ca|co)|amoi|an(ex|ny|yw)|aptu|ar(ch|go)|as(te|us)|attw|au(di|\-m|r |s )|avan|be(ck|ll|nq)|bi(lb|rd)|bl(ac|az)|br(e|v)w|bumb|bw\-(n|u)|c55\/|capi|ccwa|cdm\-|cell|chtm|cldc|cmd\-|co(mp|nd)|craw|da(it|ll|ng)|dbte|dc\-s|devi|dica|dmob|do(c|p)o|ds(12|\-d)|el(49|ai)|em(l2|ul)|er(ic|k0)|esl8|ez([4-7]0|os|wa|ze)|fetc|fly(\-|_)|g1 u|g560|gene|gf\-5|g\-mo|go(\.w|od)|gr(ad|un)|haie|hcit|hd\-(m|p|t)|hei\-|hi(pt|ta)|hp( i|ip)|hs\-c|ht(c(\-| |_|a|g|p|s|t)|tp)|hu(aw|tc)|i\-(20|go|ma)|i230|iac( |\-|\/)|ibro|idea|ig01|ikom|im1k|inno|ipaq|iris|ja(t|v)a|jbro|jemu|jigs|kddi|keji|kgt( |\/)|klon|kpt |kwc\-|kyo(c|k)|le(no|xi)|lg( g|\/(k|l|u)|50|54|\-[a-w])|libw|lynx|m1\-w|m3ga|m50\/|ma(te|ui|xo)|mc(01|21|ca)|m\-cr|me(rc|ri)|mi(o8|oa|ts)|mmef|mo(01|02|bi|de|do|t(\-| |o|v)|zz)|mt(50|p1|v )|mwbp|mywa|n10[0-2]|n20[2-3]|n30(0|2)|n50(0|2|5)|n7(0(0|1)|10)|ne((c|m)\-|on|tf|wf|wg|wt)|nok(6|i)|nzph|o2im|op(ti|wv)|oran|owg1|p800|pan(a|d|t)|pdxg|pg(13|\-([1-8]|c))|phil|pire|pl(ay|uc)|pn\-2|po(ck|rt|se)|prox|psio|pt\-g|qa\-a|qc(07|12|21|32|60|\-[2-7]|i\-)|qtek|r380|r600|raks|rim9|ro(ve|zo)|s55\/|sa(ge|ma|mm|ms|ny|va)|sc(01|h\-|oo|p\-)|sdk\/|se(c(\-|0|1)|47|mc|nd|ri)|sgh\-|shar|sie(\-|m)|sk\-0|sl(45|id)|sm(al|ar|b3|it|t5)|so(ft|ny)|sp(01|h\-|v\-|v )|sy(01|mb)|t2(18|50)|t6(00|10|18)|ta(gt|lk)|tcl\-|tdg\-|tel(i|m)|tim\-|t\-mo|to(pl|sh)|ts(70|m\-|m3|m5)|tx\-9|up(\.b|g1|si)|utst|v400|v750|veri|vi(rg|te)|vk(40|5[0-3]|\-v)|vm40|voda|vulc|vx(52|53|60|61|70|80|81|83|85|98)|w3c(\-| )|webc|whit|wi(g |nc|nw)|wmlb|wonu|x700|yas\-|your|zeto|zte\-/i.test(a.substr(0, 4))) check = true;
	})(navigator.userAgent || navigator.vendor || window.opera);
	return check;
}


function setSelectedValue(selectObj, valueToSet, valueType = false) {
	for (var i = 0; i < selectObj.options.length; i++) {
		if (valueType == true) {
			if (selectObj.options[i].value == valueToSet) {
				selectObj.options[i].selected = true;
				return;
			}
		} else {
			// alert(valueToSet + " --- " + selectObj.options[i].text);
			if (selectObj.options[i].text == valueToSet) {
				selectObj.options[i].selected = true;
				return;
			}
		}
	}
}

var PERIOD_LAST_14="Last 14 Days"
var PERIOD_LAST_30="Last 30 Days"
var PERIOD_LAST_90="Last 90 Days"
var PERIOD_LAST_YEAR="Last Year"

var PERIOD_WEEK="This Week"
var PERIOD_MONTH="Last Month"
var PERIOD_YEAR="Last Year"
var PERIOD_4H="4 Hours"
var PERIOD_12H="12 Hours"
var PERIOD_1D="1 Day"
var PERIOD_3D="3 Days"
var PERIOD_7D="7 Days"
var PERIOD_30D="30 Days"

// Returns UTC time
function get_start_time(period) {
    
    var now = new Date();
	var start = new Date(now.toUTCString().slice(0, -4));

    if (period == PERIOD_4H)
	{
        start.setHours(start.getHours() - 4);
	}
    else if ( period == PERIOD_12H ) {
		start.setHours(start.getHours() - 12);
	}
    else if ( period == PERIOD_1D ) {
		start.setDate(start.getDate() - 1);
	}
    else if ( period == PERIOD_3D ) {
		start.setDate(start.getDate() - 3);
	}
	else if ( period == PERIOD_7D ) {
		start.setDate(start.getDate() - 7);
	}
    else if ( period == PERIOD_30D ) {
        start.setDate(start.getDate() - 30);
	}
	else if ( period == PERIOD_WEEK ) {
        start.setDate(start.getDate() - 7);
	}
	else if ( period == PERIOD_MONTH ) {
        start.setDate(start.getDate() - 30);
	}
	else if ( period == PERIOD_YEAR || period == PERIOD_LAST_YEAR ) {
        start.setDate(start.getDate() - 30*12);
	}
	else if ( period == PERIOD_LAST_14 ) {
        start.setDate(start.getDate() - 14);
	}
	else if ( period == PERIOD_LAST_30 ) {
        start.setDate(start.getDate() - 30);
	}
	else if ( period == PERIOD_LAST_90 ) {
        start.setDate(start.getDate() - 90);
	}
    
    return start;
}


function get_login_status(data) {

	if ( data == "0" )
	{
	  return "Disabled";
	}
	if ( data == "1" )
	{
	  return "Lifetime";
	}
	if ( data == "2" )
	{
	  return "Limited";
	}
	if ( data == "3" )
	{
	  return "Trial";
	}
	if ( data == "4" )
	{
	  return "Subscribed";
	}
	if ( data == "5" )
	{
	  return "Non-Subscriber";
	}
	return data
}

function get_login_data(status) {

    if ( status == "Disabled" )
    {
      return "0";
    }
    if ( status == "Lifetime" )
    {
      return "1";
    }
    if ( status == "Limited" )
    {
      return "2";
    }
    if ( status == "Trial" )
    {
      return "3";
    }
    if ( status == "Subscribed" )
    {
      return "4";
    }
	if ( status == "Non-Subscriber" )
    {
      return "5";
    }
    return status
}
