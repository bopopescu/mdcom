MHSchedule.ajaxUtils = {};

MHSchedule.ajaxUtils.dateToString = function(date) {
	var month = (date.getMonth()+1).toString();
	month = (month.length == 1) ? '0'+month : month;
	
	var day = date.getDate().toString();
	day = (day.length == 1) ? '0'+day : day;
	
	var hour = date.getHours().toString();
	hour = (hour.length == 1) ? '0'+hour : hour;
	
	var minute = date.getMinutes().toString();
	minute = (minute.length == 1) ? '0'+minute : minute;
	
	var second = date.getSeconds().toString();
	second = (second.length == 1) ? '0'+second : second;
	
	return(date.getFullYear()+'-'+month+'-'+day+' '+hour+':'+minute+':'+second);
}

MHSchedule.ajaxUtils.stringToDate = function(str) {
	var year = str.substring(0,4);
	var month = parseInt(str.substring(5,7),10)-1;
	var day = str.substring(8,10);
	var hour = str.substring(11,13);
	var minute = str.substring(14,16);
	var second = str.substring(17,19);
	
	return new Date(year, month, day, hour, minute, second);
}


MHSchedule.ajaxUtils.randomString = function(length, chars) {
	if (!length) {
		length = 10;
	}
	if (!chars) {
		chars = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXTZabcdefghiklmnopqrstuvwxyz1234567890";
	}
	var randomString = '';
	for (var i=0; i<length; i++) {
		randomString += chars.charAt(Math.random() * chars.length);
	}
	return(randomString);
}
