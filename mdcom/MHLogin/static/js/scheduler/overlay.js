MHSchedule.Overlays = {};


MHSchedule.Overlays.EditHTML = '\n'+
'	<img class="close" src="{{MEDIA_URL}}images/close.gif" />'+
'	<h3 style="margin-top: 0px;"><span id="scheduleOverlay_editEvent_action"></span> On-Call</h3>'+
'	<form id="editEvent">'+
'			<input type="hidden" name="type" value="0"  />'+
'	<table border="0">'+
'	<!--<tr>'+
'		<td class="label">Type:</td>'+
'		<td>'+
'			<input type="radio" id="medical" name="type" value="0" checked="checked" /> Medical<br />'+
'			<input type="radio" id="administrative" name="type" value="1" /> Administrative<br />'+
'		</td>'+
'	</tr>-->'+
'	<tr>'+
'		<td class="label">Start:</td>'+
'		<td>'+
'			<input type="text" name="start_month" maxlength="2" size="2" />/<input type="text" name="start_day" maxlength="2" size="2" />/<input type="text" name="start_year" maxlength="4" size="4" />'+
'			at <input type="text" name="start_hour" maxlength="4" size="2" />:<input type="text" name="start_minute" maxlength="4" size="2" />'+
'			<select name="start_ampm">'+
'				<option value="0">am</option>'+
'				<option value="1">pm</option>'+
'			</select>'+
'		</td>'+
'	</tr>'+
'	<tr>'+
'		<td class="label">End:</td>'+
'		<td>'+
'			<input type="text" name="end_month" maxlength="2" size="2" />/<input type="text" name="end_day" maxlength="2" size="2" />/<input type="text" name="end_year" maxlength="4" size="4" />'+
'			at <input type="text" name="end_hour" maxlength="4" size="2" />:<input type="text" name="end_minute" maxlength="4" size="2" />'+
'			<select name="end_ampm">'+
'				<option value="0">am</option>'+
'				<option value="1">pm</option>'+
'			</select>'+
'		</td>'+
'	</tr>'+
'	<tr>'+
'		<td class="label">On-Call:</td>'+
'		<td><select name="scheduleOverlay_userList"></select></td>'+
'	</tr>'+
'	</table>'+
'	<p><a id="scheduleOverlay_editEvent_submit" href="" onclick="javascript:MHSchedule.editEventSubmit(this.form); return false;"></a> | '+
'	<a class="close" href="" onclick="return false;">Cancel</a><span id="scheduleOverlay_editEvent_delete"> | '+
'	<a class="scheduleOverlay_editEvent_delete" href="" onclick="MHSchedule.displayEventDeleteConfirmation();return false;">Delete</a></span></p>'+
'	</form>';

MHSchedule.newEventOverlay = function(startDate, endDate) {
	if (startDate == null) {
		startDate = MHSchedule.baseDate;
	}
	if (endDate == null) {
		endDate = new Date(startDate.getTime());
		
		
		var durationDays = parseInt($('form#dragged_new_event_durationconfig_form #duration_days').val(), 10);
		var durationHours = parseInt($('form#dragged_new_event_durationconfig_form #duration_hours').val(), 10);
		var durationMinutes = parseInt($('form#dragged_new_event_durationconfig_form #duration_minutes').val(), 10);
		
		// Check our inputs. First, did all the inputs parse properly?
		if (isNaN(durationDays) || isNaN(durationHours) || isNaN(durationMinutes)) {
			//alert('An invalid value was given for one of the event duration fields. All values must be numbers.');
			endDate.setHours(endDate.getHours()+1);
		}
		// Next, are the inputs all real?
		else if (durationDays < 0 || durationHours < 0 || durationMinutes < 0) {
			//alert('Only positive (or zero) values are allowed for the event duration fields.');
			endDate.setHours(endDate.getHours()+1);
		}
		//There should be a non-zero duration value.
		else if (durationDays+durationHours+durationDays == 0) {
			//alert('The given event duration is invalid. It must be greater than zero.');
			endDate.setHours(endDate.getHours()+1);
		}
		else {
			endDate.setDate(endDate.getDate()+durationDays);
			endDate.setHours(endDate.getHours()+durationHours);
			endDate.setMinutes(endDate.getMinutes()+durationMinutes);
		}
	}
	
	MHSchedule.displayEventEditor(null, startDate, endDate);
	return;
}

MHSchedule.editEvent = function(event, ui) {
	event.stopPropagation();
	
	MHSchedule.displayEventEditor(MHSchedule.findEventByDiv(this), null, null);
}

MHSchedule.displayEventEditor = function(event, startDate, endDate) {
	// if event is null, then this is creating a new event.
	
	var newEvent = true;
	var titleActionText = "New";
	var saveText = "Create";
	if (event != null) {
		newEvent = false;
		startDate = event.startDate;
		endDate = event.endDate;
		titleActionText = "Edit";
		saveText = "Apply Changes";
		$('span#scheduleOverlay_editEvent_delete').show();
		userID = event.userID;
	}
	else {
		userID = null;
		$('span#scheduleOverlay_editEvent_delete').hide();
	}
	$('div#scheduleOverlay_editEvent').overlay({

			// custom top position
			top: 'center',
			left: 'center',

			// some expose tweaks suitable for facebox-looking dialogs
			mask: {
				// you might also consider a "transparent" color for the mask
				color: '#111',
				// load mask a little faster
				loadSpeed: 200,
				opacity: 0.7
			},

			// disable this for modal dialog-type of overlays
			closeOnClick: true,
			api: true // for some reason, if api is omitted (or false), the
					  // first overlay display call is ignored.

		// load it immediately after the construction
		}).load();
	// startDate
	
	$('div#scheduleOverlay_editEvent span#scheduleOverlay_editEvent_action').html(titleActionText);
	$('a#scheduleOverlay_editEvent_submit').html(saveText);
	
	if (!newEvent) {
		//$('div#scheduleOverlay_editEvent input#medical').removeAttr('checked');
		//$('div#scheduleOverlay_editEvent input#administrative').removeAttr('checked');
		//if (event.type == 0) {
		//	$('div#scheduleOverlay_editEvent input#medical').attr('checked', 'checked');
		//}
		//else if (event.type == 1) {
		//	$('div#scheduleOverlay_editEvent input#administrative').attr('checked', 'checked');
		//}
		
		var newInputDiv = $('form#editEvent input[name=eventID]');
		if (newInputDiv.length < 1) {
			var newInputDiv = $(document.createElement('input'));
			newInputDiv.attr('name', 'eventID');
			newInputDiv.attr('type', 'hidden');
			newInputDiv.attr('value', event.id);
			
			$('form#editEvent').append(newInputDiv);
		}
		else {
			newInputDiv.attr('value', event.id);
		}
	}
	else {
		var newInputDiv = $('form#editEvent input[name=eventID]');
		if (newInputDiv.length > 0) {
			newInputDiv.remove();
		}
	}
	
	var startMonth = startDate.getMonth()+1;
	startMonth = startMonth.toString().length == 1 ? '0'+startMonth : startMonth;
	var endMonth = endDate.getMonth()+1;
	endMonth = endMonth.toString().length == 1 ? '0'+endMonth : endMonth;
	
	var startDay = startDate.getDate();
	startDay = startDay.toString().length == 1 ? '0'+startDay : startDay;
	var endDay = endDate.getDate();
	endDay = endDay.toString().length == 1 ? '0'+endDay : endDay;
	
	var startHours = startDate.getHours();
	var endHours = endDate.getHours();
	var startAMPM = startHours <= 11 ? 0 : 1;
	var endAMPM = endHours <= 11 ? 0 : 1;
	
	startHours = startHours % 12;
	startHours = startHours == 0 ? 12 : startHours;
	startHours = startHours.toString().length == 1 ? '0'+startHours.toString() : startHours;
	endHours = endHours % 12;
	endHours = endHours == 0 ? 12 : endHours;
	endHours = endHours.toString().length == 1 ? '0'+endHours : endHours;
	
	var startMinutes = startDate.getMinutes();
	startMinutes = startMinutes.toString().length == 1 ? '0'+startMinutes : startMinutes;
	var endMinutes = endDate.getMinutes();
	endMinutes = endMinutes.toString().length == 1 ? '0'+endMinutes : endMinutes;
	
	$('form#editEvent input[name=start_month]').val(startMonth);
	$('form#editEvent input[name=start_day]').val(startDay);
	$('form#editEvent input[name=start_year]').val(startDate.getFullYear());
	$('form#editEvent input[name=start_hour]').val(startHours);
	$('form#editEvent input[name=start_minute]').val(startMinutes);
	$('form#editEvent select[name=start_ampm]').val(startAMPM);
	$('form#editEvent input[name=end_month]').val(endMonth);
	$('form#editEvent input[name=end_day]').val(endDay);
	$('form#editEvent input[name=end_year]').val(endDate.getFullYear());
	$('form#editEvent input[name=end_hour]').val(endHours);
	$('form#editEvent input[name=end_minute]').val(endMinutes);
	$('form#editEvent select[name=end_ampm]').val(endAMPM);
	if (userID) {
		$('form#editEvent select[name=scheduleOverlay_userList]').val(event.userID);
	}
}


MHSchedule.viewEventDetails = function(event) {
	event.preventDefault();
}

MHSchedule.editEventSubmit = function() {
	var form = $('form#editEvent');
	var eventID = form.find('input[name=eventID]');
	var event = null;
	if (eventID.length > 0) {
		event = MHSchedule.findEventByID(eventID.val());
	}
	
	//var eventType = $('form#newEvent input[name=type]').attr("checked", "checked").val();
	//var eventType = form.find('input[name=type]:checked').val();
	var eventType = form.find('input[name=type]').val();

	var startYear = form.find('input[name=start_year]').val();
	var startMonth = form.find('input[name=start_month]').val() - 1;
	var startDay = form.find('input[name=start_day]').val();
	var startHour = form.find('input[name=start_hour]').val();
	var startMinute = form.find('input[name=start_minute]').val();
	var startAMPM = form.find('select[name=start_ampm]').val();
	if (startHour <= 12) {
		// Converting startHour to 24-hour time.
		startHour = +startHour % 12;
		startHour = +startHour + (startAMPM*12);
	}
	if (startHour == 24) {
		startHour = 0;
	}

	var endYear = form.find('input[name=end_year]').val();
	var endMonth = form.find('input[name=end_month]').val() - 1;
	var endDay = form.find('input[name=end_day]').val();
	var endHour = form.find('input[name=end_hour]').val();
	var endMinute = form.find('input[name=end_minute]').val();
	var endAMPM = form.find('select[name=end_ampm]').val();
	if (endHour <= 12) {
		// Converting endHour to 24-hour time.
		endHour = +endHour % 12;
		endHour = +endHour + (endAMPM*12);
	}
	if (endHour == 24) {
		endHour = 0;
	}
	
	var userID = $('form#editEvent select[name=scheduleOverlay_userList]').val();
	
	//alert(startMonth+"/"+startDay+"/"+startYear+" at "+startHour+":"+startMinute+" "+startAMPM);
	//alert(endMonth+"/"+endDay+"/"+endYear+" at "+endHour+":"+endMinute+" "+endAMPM);
	//alert(eventType);
	
	// Validate inputs
	if (MHSchedule.validateEventSubmission( eventType,
				startYear, startMonth, startDay, startHour, startMinute,
				endYear, endMonth, endDay, endHour, endMinute, userID)) {
		// MHSchedule.validateEventSubmission returns 1 (true) on validation fail
		return;
	}
	
	// Okay, we have a valid new on-call.
	MHSchedule.displaySaveWarning();
	++MHSchedule.undoLevels;

	if (event == null) {
		var newEvent = new MHSchedule.ScheduleEventByFields(
							'new'+MHSchedule.newEvents.length.toString(), userID, eventType,
							startYear, startMonth, startDay, startHour, startMinute,
							endYear, endMonth, endDay, endHour, endMinute);
		newEvent.newFlag = true;
		MHSchedule.newEvents.push(newEvent);
		newEvent.display();
	}
	else {
		event.changeFlag = true;
		event.changeEventType(eventType);
		event.userID = userID;
		event.changeDates(new Date(startYear, startMonth, startDay, startHour, startMinute),
							new Date(endYear, endMonth, endDay, endHour, endMinute));
	}
	
	$('div#scheduleOverlay_editEvent').overlay().close();
}

MHSchedule.validateEventSubmission = function(
		eventType,
		startYear, startMonth, startDay, startHour, startMinute,
		endYear, endMonth, endDay, endHour, endMinute, userID
		) {
	
	var numericRegex = new RegExp('^[0-9]+$');
	
	if (!(eventType == 0 || eventType == 1)) {
		alert('Invalid event type. Please try closing the create dialog and try creating a new on-call. If this error persists, please report the error.');
		alert('eventType '+eventType);
		return 1;
	}
	
	
	if (startYear.length != 4 || !(numericRegex.test(startYear)) ||
					!(startYear >= 2009 && startYear <= 2099)) {
		alert('Invalid start year. Year must be 4 digits long, contain only digits, and must be between 2009 and 2099.');
		return 1;
	}
	if (startMonth.length > 2 || !(numericRegex.test(startMonth)) ||
					!(startMonth >= 0 && startMonth <= 11)) {
		alert('Invalid start month. Month must be at most 2 digits long, contain only digits, and must be between 1 and 12.');
		return 1;
	}
	if (startDay.length > 2 || !(numericRegex.test(startDay))
					|| !(startDay >= 1 && startDay <= 31)) {
		alert('Invalid start day. Day must be at most 2 digits long, contain only digits, and must be between 1 and 31.');
		return 1;
	}
	// checkDayValidity checks the day validity given the month and year.
	if (MHSchedule.checkDayValidity(startYear, startMonth, startDay)) {
		alert('Invalid start day. Day must be valid for the given month.');
		return 1;
	}
	if (startHour.length > 2 || !(numericRegex.test(startHour))
					|| !(startHour >= 0 && startHour <= 24)) {
		alert('Invalid start hour. Hour must be at most 2 digits long, contain only digits, and must be between 0 and 24.');
		return 1;
	}
	if (startMinute.length > 2 || !(numericRegex.test(startMinute))
					|| !(startMinute >= 0 && startMinute <= 59)) {
		alert('Invalid start minute. Minutes must be at most 2 digits long, contain only digits, and must be between 0 and 59.');
		return 1;
	}
	
	
	if (endYear.length != 4 || !(numericRegex.test(endYear)) ||
					!(endYear >= 2009 && endYear <= 2099)) {
		alert('Invalid end year. Year must be 4 digits long, contain only digits, and must be between 2009 and 2099.');
		return 1;
	}
	if (endMonth.length > 2 || !(numericRegex.test(endMonth)) ||
					!(endMonth >= 0 && endMonth <= 11)) {
		alert('Invalid end month. Month must be at most 2 digits long, contain only digits, and must be between 1 and 12.');
		return 1;
	}
	if (endDay.length > 2 || !(numericRegex.test(endDay))
					|| !(endDay >= 1 && endDay <= 31)) {
		alert('Invalid end day. Day must be at most 2 digits long, contain only digits, and must be between 1 and 31.');
		return 1;
	}
	// checkDayValidity checks the day validity given the month and year.
	if (MHSchedule.checkDayValidity(endYear, endMonth, endDay)) {
		alert('Invalid end day. Day must be valid for the given month.');
		return 1;
	}
	if (endHour.length > 2 || !(numericRegex.test(endHour))
					|| !(endHour >= 0 && endHour <= 24)) {
		alert('Invalid end hour. Hour must be at most 2 digits long, contain only digits, and must be between 0 and 24.');
		return 1;
	}
	if (endMinute.length > 2 || !(numericRegex.test(endMinute))
					|| !(endMinute >= 0 && endMinute <= 59)) {
		alert('Invalid end minute. Minutes must be at most 2 digits long, contain only digits, and must be between 0 and 59.');
		return 1;
	}
	
	var startDate = new Date(startYear, startMonth, startDay, startHour, startMinute);
	var endDate = new Date(endYear, endMonth, endDay, endHour, endMinute);
	
	if (endDate <= startDate) {
		alert('Invalid time range. The end date and time must come after the start date and time.');
		return 1;
	}
	
	for (id in MHSchedule.availableUsers) {
		if (userID == id) {
			return 0;
		}
	}
	
	// User ID isn't in the set of valid user IDs. reject it.
	alert('Invalid user. It looks like the selected user doesn\'t belong to your call group.');
	return 1;
}
MHSchedule.checkDayValidity = function(year, month, day) {
	// Returns True if day is invalid for given month and year.
	if (day > 31 || day < 1) {
		return 1;
	}
	if (month < 7) {
		if (month == 1) {
			// February. Check year.
			if (year % 4 == 0) {
				if (year % 100 == 0) {
					if (year % 400 == 0 && day > 29) {
						return 1;
					}
					if (day > 28) {
						return 1;
					}
				}
				else {
					if (day > 29) {
						return 1;
					}
				}
			}
			else {
				if (day > 28) {
					return 1;
				}
			}
		}
		if (month %2 == 1 && day == 31) {
			return 1;
		}
		return 0;
	}
	// Month > 8.
	if (month % 2 == 0 && day == 31) {
		return 1;
	}
	return 0;
}


MHSchedule.displayEventDeleteConfirmation = function(eventID) {
	// hide the editEvent schedule overlay.
	$('div#scheduleOverlay_editEvent').overlay().close();
	
	// Now, display the new overlay.
	setTimeout('MHSchedule.displayEventDeleteConfirmation_ShowDiv('+eventID+')', 250);
	
}
MHSchedule.displayEventDeleteConfirmation_ShowDiv = function(eventID) {
	if (!eventID) {
		eventID = $('form#editEvent').find('input[name=eventID]').val();
	}
	var event = MHSchedule.findEventByID(eventID);
	
	var startMonth = event.startDate.getMonth()+1;
	startMonth = startMonth.toString().length == 1 ? '0'+startMonth : startMonth;
	var endMonth = event.endDate.getMonth()+1;
	endMonth = endMonth.toString().length == 1 ? '0'+endMonth : endMonth;
	
	var startDay = event.startDate.getDate();
	startDay = startDay.toString().length == 1 ? '0'+startDay : startDay;
	var endDay = event.endDate.getDate();
	endDay = endDay.toString().length == 1 ? '0'+endDay : endDay;
	
	var startHours = event.startDate.getHours();
	var endHours = event.endDate.getHours();
	var startAMPM = startHours <= 11 ? 'AM' : 'PM';
	var endAMPM = endHours <= 11 ? 'AM' : 'PM';
	
	startHours = startHours % 12;
	startHours = startHours == 0 ? 12 : startHours;
	startHours = startHours.toString().length == 1 ? '0'+startHours.toString() : startHours;
	endHours = endHours % 12;
	endHours = endHours == 0 ? 12 : endHours;
	endHours = endHours.toString().length == 1 ? '0'+endHours : endHours;
	
	var startMinutes = event.startDate.getMinutes();
	startMinutes = startMinutes.toString().length == 1 ? '0'+startMinutes : startMinutes;
	var endMinutes = event.endDate.getMinutes();
	endMinutes = endMinutes.toString().length == 1 ? '0'+endMinutes : endMinutes;
	
	startTD = $('span#deleteConfirmOverlay_start');
	startTD.empty();
	startTD.html(startMonth+'/'+startDay+'/'+event.startDate.getFullYear()+
			' at '+startHours+':'+startMinutes+' '+startAMPM);
	
	endTD = $('span#deleteConfirmOverlay_end');
	endTD.empty();
	endTD.html(endMonth+'/'+endDay+'/'+event.endDate.getFullYear()+
			' at '+endHours+':'+endMinutes+' '+endAMPM);
	
	userTD = $('span#deleteConfirmOverlay_onCall');
	userTD.empty();
	userTD.html(MHSchedule.availableUsers[event.userID]['first_name']+' '+MHSchedule.availableUsers[event.userID]['last_name']);
	
	overlay = $('div#scheduleOverlay_deleteEvent').overlay({

			// custom top position
			top: 'center',
			left: 'center',

			// some expose tweaks suitable for facebox-looking dialogs
			mask: {
				// you might also consider a "transparent" color for the mask
				color: '#111',
				// load mask a little faster
				loadSpeed: 200,
				opacity: 0.7
			},

			// disable this for modal dialog-type of overlays
			closeOnClick: true,
			api: true // for some reason, if api is omitted (or false), the
					  // first overlay display call is ignored.

		// load it immediately after the construction
		}).load();
}
MHSchedule.deleteEvent = function(eventID) {
	// Now, "delete" the event.
	if (!eventID) {
		eventID = $('form#editEvent').find('input[name=eventID]').val();
	}
	MHSchedule.displaySaveWarning();
	var event = MHSchedule.findEventByID(eventID);
	event.delEvent();
	// hide the editEvent schedule overlay.
	$('div#scheduleOverlay_deleteEvent').overlay().close();
}
//Add new overlay by kada.xinl 20110913
MHSchedule.editConflict = function(){
	$('#overlapConflict').overlay({
		top: 'center',
		left: 'center',
		mask: {
			color: '#111',
			loadSpeed: 200,
			opacity: 0.7
		},
		closeOnClick: true
	});
}