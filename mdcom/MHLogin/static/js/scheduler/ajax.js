// Storage object for metadata/bookkeeping used by this module.
//fixed feature 277 by xlin 20111103

MHSchedule.ajax = {};

// Metadata for getEvents -- this will keep track of all of the date ranges
// that we've fetched so far. The ranges will be stored as date pairs, e.g.:
// MHSchedule.ajax.eventDatesCached[0] = [startDate, endDate];
MHSchedule.ajax.eventDatesCached = [];
MHSchedule.getEvents = function(startDate, endDate) {
	/* Fetches events for the given date range, if they haven't already been
	 * fetched. This function should always be called on calendar date changes
	 * so that the cached date range can be maintained in a single location.
	 * 
	 * This function fetches a minimum of a 30 days at a time in order to 
	 * minimize queries.
	 */
	
	// These variables shall contain the new values for eventDatesCached, so
	// that we can apply the cached date changes IFF the AJAX call was
	// successful.
	var newCacheStart;
	var newCacheEnd;
	// Check to ensure that this date range hasn't been fetched yet.
	if (MHSchedule.ajax.eventDatesCached.length == 2) {
		var cachedStart = MHSchedule.ajax.eventDatesCached[0];
		var cachedEnd = MHSchedule.ajax.eventDatesCached[1];
		
		if (cachedStart <= startDate && cachedEnd >= endDate) {
			return; // Don't fetch anything, as we already have events for the range.
		}
		if (cachedStart > startDate) {
			// The user is getting an earlier time period than we've cached.
			
			// Set the end date to the cached start date
			endDate = cachedStart;
			
			// Okay, now enforce the minimum time period for fetches.
			if (endDate.getTime() - startDate.getTime() <= 2592000000) { // 2,592,000,000 milliseconds in 30 days
				startDate = new Date(endDate);
				startDate.setDate(startDate.getDate()-30);
			}
			
			// And update our bookkeeping
			newCacheStart = new Date(startDate);
			newCacheEnd = MHSchedule.ajax.eventDatesCached[1];
		}
		else { // (cachedEnd < endDate)
			// The user is getting a later time period than we've cached.
			
			// Set the start date to the cached end date
			startDate = cachedEnd;
			
			// Okay, now enforce the minimum time period for fetches.
			if (endDate.getTime() - startDate.getTime() <= 2592000000) { // 2,592,000,000 milliseconds in 30 days
				endDate = new Date(startDate);
				endDate.setDate(endDate.getDate()+30);
			}
			
			// And update our bookkeeping
			newCacheStart = MHSchedule.ajax.eventDatesCached[0];
			newCacheEnd = new Date(endDate);
		}
	}
	else { // MHSchedule.ajax.eventDatesFetched.length == 0
		if (endDate.getTime() - startDate.getTime() <= 2592000000) { // 2,592,000,000 milliseconds in 30 days
			endDate = new Date(startDate);
			endDate.setDate(endDate.getDate()+30);
		}
		newCacheStart = new Date(startDate);
		newCacheEnd = new Date(endDate);
	} // end if (MHSchedule.ajax.eventDatesFetched.length == 2)
	

	$.ajax({
		url: 'AJAX/getEvents/',
		type: 'POST',
		data: {
			fromDate:MHSchedule.ajaxUtils.dateToString(startDate),
			toDate:MHSchedule.ajaxUtils.dateToString(endDate)
		}, // end data
		
		success: function(data, textStatus, httpRequest) {
			// Test for success
			if (textStatus == 'success') {
	
				for (var idx=0; idx<data.length; idx++) {
					jsonEvent = data[idx];
					if (MHSchedule.events[jsonEvent.pk]) {
						// This event already exists. Don't go creating a new copy.
						continue;
					}
					MHSchedule.events[jsonEvent.pk] =
						new MHSchedule.ScheduleEvent(
							jsonEvent.pk,
							parseInt(jsonEvent.fields['oncallPerson']),
							parseInt(jsonEvent.fields['eventType']),
							MHSchedule.ajaxUtils.stringToDate(jsonEvent.fields['startDate']),
							MHSchedule.ajaxUtils.stringToDate(jsonEvent.fields['endDate']),
							jsonEvent.fields['checkString']
						);
					MHSchedule.events[jsonEvent.pk].reposition();
				}
				MHSchedule.ajax.eventDatesCached[0] = newCacheStart;
				MHSchedule.ajax.eventDatesCached[1] = newCacheEnd;
			}
		}, // end success
		error: function(httpRequest, textStatus, errorThrown) {
			alert('an error occurred getting the events.');
		}
	});
	
	
	/* to add more testing events, follow the given format:
	 * events[ID] = new MHSchedule.ScheduleEvent(ID, eventType,
	 * 		startYear, startMonth, startDay, startHour, startMinute,
	 * 		endYear, endMonth, endDay, endHour, endMinute);
	 * 
	 * Where... (for things that require notes)
	 * 		ID: The ID of the given object. This must be unique.
	 * 		eventType: 0 for medical, 1 for administrative
	 *		(start|end)Month: Standard month #, minus one (0-11)
	 */

/*
	// Basic test -- Type 0
	MHSchedule.events[15] = new MHSchedule.ScheduleEvent(15, 2, 0,
					new Date(2010, 10, 11, 18, 00),
					new Date(2010, 10, 12, 06, 00)
				);
	MHSchedule.events[22] = new MHSchedule.ScheduleEventByFields(22, 2, 0,
						2010, 10, 7, 2, 00,
						2010, 10, 7, 8, 00);
	// Basic test -- Type 1
	MHSchedule.events[23] = new MHSchedule.ScheduleEventByFields(23, 42, 0,
						2010, 10, 5, 18, 00,
						2010, 10, 6, 8, 00);
	MHSchedule.events[26] = new MHSchedule.ScheduleEventByFields(26, 2, 0,
						2010, 10, 7, 8, 00,
						2010, 10, 8, 18, 00);
	MHSchedule.events[27] = new MHSchedule.ScheduleEventByFields(27, 43, 0,
						2010, 10, 2, 2, 15,
						2010, 10, 2, 5, 00);
	
	
	MHSchedule.events[24] = new MHSchedule.ScheduleEventByFields(24, 42, 0,
						2010, 10, 3, 3, 00,
						2010, 10, 3, 4, 00);
	// Basic test -- Type 1
	MHSchedule.events[25] = new MHSchedule.ScheduleEventByFields(25, 2323, 0,
						2010, 10, 1, 1, 00,
						2010, 10, 1, 2, 00);
*/
}


MHSchedule.refreshCallGroupMembers = function() {
	// First, get the list of available members.
	$.ajax({
		url: '../AJAX/getMembers/',
		type: 'POST',
		
		success: function(data, textStatus, httpRequest) {
			// Test for success
			if (textStatus == 'success') {
				// Clear the current availableUsers list and color assignments.
				MHSchedule.availableUsers = {};
				MHSchedule.userColorsAssigned = {};
				MHSchedule.userColorsAssignedCounter = 0;
				for (var idx=0; idx<data.length; idx++) {
					user = data[idx];
					//console.dir(idx+'  '+user) ;
					//#180 Color and user older Chen Hu 
					MHSchedule.availableUsers[user[0]] = {
						id: user[0],
						first_name: user[1],
						last_name: user[2],
						index:idx
					};
					//alert(MHSchedule.availableUsers[user[0]].id);
					//console.dir(MHSchedule.availableUsers) ;
					MHSchedule.userColorsAssigned[user[0]] = MHSchedule.userColorsAvailable[MHSchedule.userColorsAssignedCounter];
					++MHSchedule.userColorsAssignedCounter;
					
				}
				MHSchedule.displayCallGroupMembers();
				MHSchedule.currentModule.showEvents();
			}
		}, // end success
		error: function(httpRequest, textStatus, errorThrown) {
			alert('An error occurred getting a list of call group users.');
			$('div#errorDebug').html(httpRequest.responseText);
			return;
		}
	});
}

MHSchedule.displayCallGroupMembers = function() {
	// Next, clear the existing user spans
	var userDivs = $('div#calendar_available_users div.calendar_user');
	userDivs.remove();
	
	var userListDiv = $('#calendar_available_users');
	
	var overlaySelect = $('form#editEvent select[name=scheduleOverlay_userList]');
	overlaySelect.empty();
	
	var helperParentDiv = $('calendar_navColumnContainer');
	
	// Now, display users.
	var color_idx = 0;
	var userSpanTexts = '';

	//add for chrome
	var UserIdArray = new Array();
	var tempIndex = 0;

	//180 color and member order Chen Hu
	for(var id in MHSchedule.availableUsers)
	{
		UserIdArray[MHSchedule.availableUsers[id].index] = id;
	}
	//for (var id in MHSchedule.availableUsers) {
	
	
	//180 color and member order Chen Hu
	for (var i=0; i<UserIdArray.length; i++) {
		id = UserIdArray[i];
		// First, add the user to the draggable available users list.
		/*var userSpan = $(document.createElement('span'));
		userSpan.addClass('calendar_user');
		userSpan.attr('id', 'calendar_user_'+id);
		userSpan.attr('userID', id);
		userSpan.attr('color', MHSchedule.userColorsAvailable[color_idx]);
		userSpan.html(MHSchedule.availableUsers[id]['first_name']+' '+MHSchedule.availableUsers[id]['last_name']+'<br />');
		
		// Style
		userSpan.css('background-color', [id]);
		++color_idx;*/
		if(id==null)
		{
			continue;
		}

		var userSpan = '<span class="calendar_user" userID="'+id+'" color="'+
			MHSchedule.userColorsAvailable[color_idx]+
			'" style="background-color:'+
			MHSchedule.userColorsAvailable[color_idx]+'">'+
			MHSchedule.availableUsers[id]['first_name']+' '+
			MHSchedule.availableUsers[id]['last_name']+'</span><br />';
		++color_idx;
		
		userSpanTexts+=userSpan;

		
		// Next, add the user to the users select in the overlay.
		userSpan = $(document.createElement('option'));
		userSpan.attr('value', id);
		userSpan.html(MHSchedule.availableUsers[id]['first_name']+' '+MHSchedule.availableUsers[id]['last_name']);
		overlaySelect.append(userSpan);
	}
	userListDiv.html(userSpanTexts);
	
	// Event Handler
	$('span.calendar_user').draggable({
		addClasses: false,
		revert: 'invalid',
		containment: '#content_div',
		helper: 'clone',

		appendTo: '#content_div',
		scroll: false
		//zIndex: 999
		//grid: [MHSchedule.currentModule.slotWidth,1],
		
		//stop: MHSchedule.currentModule.dragEventHandler
		// The following is disabled. It looks like the div text doesn't
		// automagically update during the drag.
		// drag: updateEventDivText_EventHandler,
	});
	
	/* IE refresh workaround:
	 * IE has issues when drawing the available users div and needs the div to
	 * be manually refreshed. For some reason, one or none of the user spans
	 * display by default when overflow is set to auto.
	 */
	setTimeout(function() {
		userListDiv.css('display', 'none');
		userListDiv.css('display', 'block');
	}, 250);
	
	// Event Handler
	$('.calendar_user').draggable({
		//addClasses: false,
		revert: 'invalid',
		containment: '#content_div',
		helper: 'clone',

		appendTo: '#content_div',
		scroll: false
		//zIndex: 999
		//grid: [MHSchedule.currentModule.slotWidth,1],
		
		//stop: MHSchedule.currentModule.dragEventHandler
		// The following is disabled. It looks like the div text doesn't
		// automagically update during the drag.
		// drag: updateEventDivText_EventHandler,
	});
	
	$('#calendar_display').droppable({
		accept: '.calendar_user',
		drop: function(event, ui) {
			var dropped = true;
			//$.ui.ddmanager.current.cancelHelperRemoval = true;
			//ui.helper.appendTo(this);
			
			/* First, determine which mode the user's in. We have either
			 * specification of start & end times, or duration. Once
			 * we've determined how the user wishes to constrain new
			 * event generation, we'll set durationDays, durationHours,
			 * and durationMinutes accordingly. Additionally, if the
			 * user wishes to specify a start time, that will be passed
			 * as well.
			 */
			
			// Getting the active accordion pane using the following
			// method since the jQueryUI method seems to always return
			// null. This is likely a bug.
			if ($("#dragged_new_event_config p").index($("p.ui-state-active")) == 0) {
				
				// The user is giving a start & end time.
				var startHours = parseInt($('form#dragged_new_event_timesconfig_form #dragged_new_event_start_hours').val(), 10);
				var startMinutes = parseInt($('form#dragged_new_event_timesconfig_form #dragged_new_event_start_minutes').val(), 10);
				if ($('form#dragged_new_event_timesconfig_form #dragged_new_event_start_ampm').val() == 2 && startHours < 12) {
					// the user selected "pm" and adding 12 hours won't send us over 24.
					startHours += 12;
				}
				else if ($('form#dragged_new_event_timesconfig_form #dragged_new_event_start_ampm').val() == 1 && startHours == 12) {
					// the user selected "AM" and entered 12 for hours.
					startHours = 0;
				}
				
				var endHours = parseInt($('form#dragged_new_event_timesconfig_form #dragged_new_event_end_hours').val(), 10);
				var endMinutes = parseInt($('form#dragged_new_event_timesconfig_form #dragged_new_event_end_minutes').val(), 10);
				if($('form#dragged_new_event_timesconfig_form #dragged_new_event_end_ampm').val() == 2 && endHours < 12) {
					// the user selected "pm" and adding 12 hours won't send us over 24.
					endHours += 12;
				}
				else if ($('form#dragged_new_event_timesconfig_form #dragged_new_event_end_ampm').val() == 1 && endHours == 12) {
					// the user selected "AM" and entered 12 for hours.
					endHours = 0;
				}
				MHSchedule.currentModule.draggedNewUserEventHandler_byTime(event, ui, startHours, startMinutes, endHours, endMinutes);
			}
			else {
				// The user is strictly giving a duration.
				var durationDays = parseInt($('form#dragged_new_event_durationconfig_form #duration_days').val(), 10);
				var durationHours = parseInt($('form#dragged_new_event_durationconfig_form #duration_hours').val(), 10);
				var durationMinutes = parseInt($('form#dragged_new_event_durationconfig_form #duration_minutes').val(), 10);
				
				// Check our inputs. First, did all the inputs parse properly?
				if (isNaN(durationDays) || isNaN(durationHours) || isNaN(durationMinutes)) {
					alert('An invalid value was given for one of the event duration fields. All values must be numbers.');
					return;
				}
				// Next, are the inputs all real?
				if (durationDays < 0 || durationHours < 0 || durationMinutes < 0) {
					alert('Only positive (or zero) values are allowed for the event duration fields.');
					return;
				}
				//There should be a non-zero duration value.
				if (durationDays+durationHours+durationDays == 0) {
					alert('The given event duration is invalid. It must be greater than zero.');
					return;
				}
				MHSchedule.currentModule.draggedNewUserEventHandler_byDuration(event,ui, durationDays, durationHours, durationMinutes);
			}
			$('#calendar_display .ui-draggable').droppable({
			//$('#calendar_display').droppable({
				over:function(event,ui){
					$(this).css({
						'color':'#f00'
					});
				},
				out:function(event,ui){
					$(this).css({
						'color':'#000'
					});
				}
			});
		}
	});
	
}





// Communication library for the scheduler
MHSchedule.saveSchedule_vars = {}
// Restore the changes warning/save message.
MHSchedule.saveSchedule_vars.saveText = $('#calendar_save_warning').html();
MHSchedule.saveSchedule = function(step, value) {
	if (!step) {
		$('#calendar_save_warning').html('Saving changes....');
		MHSchedule.saveSchedule_vars.failure = 0;
		MHSchedule.saveUpdatedEvents();
	}
	else if (step == 1) {
		MHSchedule.saveSchedule_vars.failure += value;
		MHSchedule.saveNewEvents();
	}
	else if (step == 2 && value == 0) {
		if (!MHSchedule.saveSchedule_vars.failure) {
			$('#calendar_save_warning').hide(500);
			// Restore the changes warning/save message.
			$('#calendar_save_warning').html(MHSchedule.saveSchedule_vars.saveText);
			MHSchedule.undoLevels = 0;
			
			for (key in MHSchedule.events){
				if (MHSchedule.events[key].undoJQueryDiv.length != 0) {
					if (MHSchedule.events[key].deleteFlag) {
						delete MHSchedule.events[key];
						continue;
					}
					
					MHSchedule.events[key].undoCleanup;
				}
			}
		}
		MHSchedule.rulecheckEvents();
	}
	else if ( step == 3 ) {
		MHSchedule.saveSchedule_vars.failure += value;
	}
	else {
		alert('step is '+step+' and value is '+value);
	}
}

MHSchedule.saveNewEvents = function() {
	// Check to see if there are any new events. If there aren't, just return.
	if (MHSchedule.newEvents.length == 0) {
		return MHSchedule.saveSchedule(2, 0); // returning 0 (success)
	}
	
	// Build JSON for the new events.
	var newEvents = MHSchedule.newEvents;
	var newEventsJSON = [];
	var newEventsByCheckString = {};
	for (var idx=0; idx<MHSchedule.newEvents.length; idx++) {
		if (newEvents[idx].deleteFlag) {
			// New event was deleted. Clear it and move on.
			newEvents[idx] = null;
			continue;
		}
		newEventsJSON[idx] = {
			pk: null,
			model: newEvents[idx].model,
			fields: {
				oncallPerson: newEvents[idx].userID,
				eventType: newEvents[idx].type,
				startDate: MHSchedule.ajaxUtils.dateToString(newEvents[idx].startDate),
				endDate: MHSchedule.ajaxUtils.dateToString(newEvents[idx].endDate),
				checkString: newEvents[idx].checkString
			}
		};
		newEventsByCheckString[newEvents[idx].checkString] = newEvents[idx];
	}
	// Convert the array and all nested objects into JSON text.
	newEventsJSON = JSON.stringify(newEventsJSON);
	$("#calendar_save_warning").text();
	
	$.ajax({
		url: 'AJAX/newEvents/',
		type: 'POST',
		data: {
			data:newEventsJSON
		}, // end data
		
		success: function(data, textStatus, httpRequest) {
			// Test for success
			if (textStatus == 'success') {
				for (var checkString in data.data) {
					pk = data.data[checkString];
					newEventsByCheckString[checkString].pk = pk;
					MHSchedule.events[pk] = newEventsByCheckString[checkString];
					MHSchedule.events[pk].id = pk;
					MHSchedule.events[pk].reposition();
				}
				MHSchedule.newEvents = [];
				$('#calendar_save_warning').hide(500);
				return MHSchedule.saveSchedule(2, 0); // returning 0 (success)
			}
		}, // end success
		error: function(httpRequest, textStatus, errorThrown) {
			alert('An error occurred adding new events. The page will reload.');
			 window.location.reload();
			//MHSchedule.displayErrorInPopup(httpRequest.responseText);
			//return MHSchedule.saveSchedule(2, 1); // returning 1
		}
	});
}

MHSchedule.saveUpdatedEvents = function () {
	// Find and store all changed events
	var changedEvents = [];
	var deletedEvents = []; // Saving these so we can prune them later.
	for (key in MHSchedule.events) {
		if (MHSchedule.events[key].changeFlag) {
			if (MHSchedule.events[key].deleteFlag) {
				deletedEvents.push(key);
			}
			changedEvents.push(MHSchedule.events[key]);
		}
	}
	
	if (changedEvents.length == 0) {
		return MHSchedule.saveSchedule(1, 0); // returning 0 (success)
	}
	
	// Okay, now build JSON for the changed events.
	var changedEventsJSON = [];
	for (var idx=0; idx<changedEvents.length; idx++) {
		changedEventsJSON[idx] = {
			pk: changedEvents[idx].id,
			model: changedEvents[idx].model,
			fields: {
				oncallPerson: changedEvents[idx].userID,
				eventType: changedEvents[idx].type,
				startDate: MHSchedule.ajaxUtils.dateToString(changedEvents[idx].startDate),
				endDate: MHSchedule.ajaxUtils.dateToString(changedEvents[idx].endDate),
				eventStatus: (changedEvents[idx].deleteFlag) ? 0 : 1,
				checkString: changedEvents[idx].checkString
			}
		};
	}
	// Convert the array and all nested objects into JSON text.
	changedEventsJSON = JSON.stringify(changedEventsJSON);
	
	$.ajax({
		url: 'AJAX/updateEvents/',
		type: 'POST',
		data: {
			data:changedEventsJSON
		}, // end data
		
		success: function(data, textStatus, httpRequest) {
			// Test for success
			if (textStatus == 'success') {
				for (var idx=0; idx<deletedEvents.length; idx++) {
					delete MHSchedule.events[deletedEvents[idx]];
				}
				//hide yellow box
				$('#calendar_save_warning').hide(500);
				return MHSchedule.saveSchedule(1, 0); // returning 0 (success)
			}
		}, // end success
		error: function(httpRequest, textStatus, errorThrown) {
			alert('An error occurred updating existing events. The page will reload.');
			 window.location.reload();
			//MHSchedule.displayErrorInPopup(httpRequest.responseText);
			//return MHSchedule.saveSchedule(1, 1); // returning 1
		}
	});
}

MHSchedule.rulecheckEvents = function() {
	/* checks events for the given date range, if there are any holes in coverage
	 * This function should always be called after updates to check for holes in coverage
	 * 
	 */
	
	$.ajax({
		url: 'AJAX/rulesCheck/',
		type: 'POST',
		data: {
//			fromDate:MHSchedule.ajaxUtils.dateToString(startDate),
//			toDate:MHSchedule.ajaxUtils.dateToString(endDate)
		}, // end data
		
		success: function(data, textStatus, httpRequest) {
			// Test for success
			var warnings = [];
			if (textStatus == 'success') {
				for ( var warning in data ) {
					// we need to list out the warnings
				}
				MHSchedule.displayErrorInPopup(httpRequest.responseText);
			}
			return MHSchedule.saveSchedule(3,0); // returning success
		}, // end success
		error: function(httpRequest, textStatus, errorThrown) {
			alert('an error occurred rules checking events.');
			return MHSchedule.saveSchedule(3, 1); // returning 1
		}
	});
}

MHSchedule.displayErrorInPopup = function(html) {
	//MHSchedule.errWin = window.open('', '', 'width=800,height=600,scrollbars=yes,toolbar=yes');
	//MHSchedule.errWin.document.write(html);
}

MHSchedule.downloadPDF = function(){
	var year = parseInt($('#calendar .year').text());
	var month = 0;
	$("#calendar td").each(function(i){
		if($(this).hasClass("currentMonth")){
			month = i + 1;
		}
	});
	var groupId = location.href.split('/')[4];
	MHSchedule.ajaxDownloadPDF(groupId,year,month);
}

MHSchedule.ajaxDownloadPDF = function(id,year,month){
	//pop dialog downloading
	//var dialog = jWait({
//		title: "Waiting for file downloading...",
//		message: "We are downloading the PDF file.",
//		zIndex:10000,
//		cancelEnable: false,
//		draggable: false
//	});
	
	if(isIPad()){
		window.open("/CallGroup/" + id + "/Schedule/Print/?year=" + year + "&month=" + month);
	}else{
		location.href="/CallGroup/" + id + "/Schedule/Print/?year=" + year + "&month=" +  month
	}
	
	//$.ajax({
//		url:"/CallGroup/" + id + "/Schedule/Print/?year=" + year + "&month=" + month,
//		success:function (data, textStatus) {
//			isSendAjax = true;
//			dialog.dialog("close");
//		},
//		error:function (data, textStatus) {
//			isSendAjax = true;
//			alert('An error occurred during the download');
//		}
//	});
}

MHSchedule.downloadPDFDialog = function(){
	$('#downloadPDFDialog').overlay().load();
}

MHSchedule.clickPrevYear = function(currentYear){
	var y = parseInt($('#calendar .year').text());
	if(y > currentYear - 5 ){
		y = y -1;
	}
	$('#calendar .year').text(y);
}

MHSchedule.clickNextYear = function(currentYear){
	var y = parseInt($('#calendar .year').text());
	if(y < currentYear + 10){
		y = y +1;
	}
	$('#calendar .year').text(y);
}
