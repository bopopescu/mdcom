

MHSchedule.utils = {};

MHSchedule.utils.findEventByDiv = function(div) {
	// Note: This is a pretty pointless function as it's easy to look up
	// the events by div. Nevertheless, please use it as divID-event mappings
	// will become more complex in the future, and this will allow us to make
	// changes more easily.
	var eventID = div.getAttribute('id').substring(5);
	
	if (eventID.length > 3) {
		// Check to see if this is a new event
		var newString = eventID.substring(0,3);
		if (newString == "new") {
			eventID = eventID.substring(3);
			eventID = parseInt(eventID);
			return (MHSchedule.newEvents[eventID]);
		}
	}
	
	eventID = parseInt(eventID);
	
	return (MHSchedule.events[eventID]);
}
// MHSchedule.findEventByDiv is obsoleted. Please use MHSchedule.utils.findEventByDiv.
MHSchedule.findEventByDiv = MHSchedule.utils.findEventByDiv;


MHSchedule.findEventByID = function(id) {
	// Note: This is a pretty pointless function as it's easy to look up
	// the events by div. Nevertheless, please use it as divID-event mappings
	// will become more complex in the future, and this will allow us to make
	// changes more easily.
	var eventID = id;
	if (eventID.length > 3) {
		// Check to see if this is a new event
		var newString = eventID.substring(0,3);
		if (newString == "new") {
			eventID = eventID.substring(3);
			eventID = parseInt(eventID);
			return (MHSchedule.newEvents[eventID]);
		}
	}
	eventID = parseInt(eventID);
	return MHSchedule.events[eventID];
}
// MHSchedule.findEventByID is obsoleted. Please use MHSchedule.utils.findEventByID.
//MHSchedule.findEventByID = MHSchedule.utils.findEventByID;



MHSchedule.DaysDifference = function(date1, date2) {
	/* Returns the number of days between the two dates. Note that this strips
	 * the time off any dates given, and goes strictly based on the dates.
	 */
	
	var cleanedDate1 = new Date(date1.getTime());
	var cleanedDate2 = new Date(date2.getTime());
	
	var daysDelta = Math.abs(cleanedDate1.getTime() - cleanedDate2.getTime());
	// 86400000 is the number of milliseconds in a typical day.
	daysDelta /= 86400000;
	// Return the rounded number of days -- this handles daylight savings, leap
	// seconds, etc. You need to accrue 12 hours of extra (or less) time for
	// this function to be incorrect.
	return Math.round(daysDelta);
}


MHSchedule.utils.DateToString = function(date) {
	var str = date.toDateString();
}
