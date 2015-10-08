
MHSchedule.WeekModule = {};

// The following timeWidth value should be configured to be dynamic based on
// the container div's size.
MHSchedule.WeekModule.timeWidth = 73; // Width of the time (hour) column.
MHSchedule.WeekModule.timeWidthOffset = MHSchedule.WeekModule.timeWidth; // How many pixels to offset for the time(hour) column.
MHSchedule.WeekModule.slotWidth = 76; // Width of the columns for each day.
MHSchedule.WeekModule.eventBorderCompensation = 4; // 5 to compensate for 2*2px borders + 1 pixel of vertical grid line
	
MHSchedule.WeekModule.totalHeight = 900;
MHSchedule.WeekModule.minPerPixel = 1440/MHSchedule.WeekModule.totalHeight;
MHSchedule.WeekModule.blockSize = Math.round(30/MHSchedule.WeekModule.minPerPixel);
// The following re-definitions are important because totalHeight (to this
// point) is an approximate target size. Due to rounding issues, we often end up
// with an actual calendar height that's greater than totalHeight. Really, what
// we're doing here is defining the calendar based on the blockSize, which is
// calculated from totalHeight, and which will get us close to totalHeight.
MHSchedule.WeekModule.totalHeight = 48*MHSchedule.WeekModule.blockSize;
MHSchedule.WeekModule.minPerPixel = MHSchedule.WeekModule.blockSize/30


// This function shall switch the scheduler to weekly mode.
MHSchedule.WeekModule.switchModes = function() {
	MHSchedule.currentModule = MHSchedule.WeekModule;
}

// The following function changes the week
MHSchedule.WeekModule.changeDates = function(dates) {

	var tempDate = new Date(dates[0]);
	$('div.calendar_display_header_text span#calendar_header_date0').html((tempDate.getMonth()+1)+'/'+tempDate.getDate());
	tempDate.setDate(tempDate.getDate()+1);
	$('div.calendar_display_header_text span#calendar_header_date1').html((tempDate.getMonth()+1)+'/'+tempDate.getDate());
	tempDate.setDate(tempDate.getDate()+1);
	$('div.calendar_display_header_text span#calendar_header_date2').html((tempDate.getMonth()+1)+'/'+tempDate.getDate());
	tempDate.setDate(tempDate.getDate()+1);
	$('div.calendar_display_header_text span#calendar_header_date3').html((tempDate.getMonth()+1)+'/'+tempDate.getDate());
	tempDate.setDate(tempDate.getDate()+1);
	$('div.calendar_display_header_text span#calendar_header_date4').html((tempDate.getMonth()+1)+'/'+tempDate.getDate());
	tempDate.setDate(tempDate.getDate()+1);
	$('div.calendar_display_header_text span#calendar_header_date5').html((tempDate.getMonth()+1)+'/'+tempDate.getDate());
	tempDate.setDate(tempDate.getDate()+1);
	$('div.calendar_display_header_text span#calendar_header_date6').html((tempDate.getMonth()+1)+'/'+tempDate.getDate());
	
	MHSchedule.baseDate = new Date(dates[0]);
	MHSchedule.endDate = new Date(MHSchedule.baseDate);
	MHSchedule.endDate.setDate(MHSchedule.endDate.getDate()+7);
	
	MHSchedule.getEvents(MHSchedule.baseDate, MHSchedule.endDate);
	
	MHSchedule.clearAllEvents();
	calendarDiv = $("div#calendar_display").empty(); // remove all child elements of the calendar
	MHSchedule.WeekModule.showCalendar();
	MHSchedule.WeekModule.showEvents();
	$("div#calendar_display").click(MHSchedule.WeekModule.newEventHandler);
}

MHSchedule.WeekModule.showCalendar = function() {
	var timeWidth = MHSchedule.WeekModule.timeWidth;
	var slotWidth = MHSchedule.WeekModule.slotWidth;
	
	var totalHeight = MHSchedule.WeekModule.totalHeight;
	var minPerPixel = MHSchedule.WeekModule.minPerPixel;
	
	// build a new div.
	//var calDiv = $(document.createElement('div'));
	//calDiv.attr('id', 'calendar_display');
	calDiv = $('#calendar_display');
	
	var ampm = ['am', 'pm'];
	for (var i = 0; i < 24; i++) {
		
		var tempDiv = $(document.createElement('div'));
		tempDiv.addClass('calendar_time');
		tempDiv.css({
					// 2*(30/minPerPixel) is needed due to rounding errors as compared to 60/minPerPixel
					'top':(i*2*MHSchedule.WeekModule.blockSize)+'px',
					'height':2*MHSchedule.WeekModule.blockSize-1+'px'
				});
		var time = (((i+11)%12)+1)+":00 "+ampm[parseInt(i/12)];
		tempDiv.attr('id', 'calendar_time_'+time);
		tempDiv.html(time);
		
		calDiv.append(tempDiv);
	}
	
	for (var day=0; day < 7; day++) {
		for (var i = 0; i < 48; i ++) { // half-hours
			var tempDiv = $(document.createElement('div'));
			tempDiv.addClass('calendar_slot');
			tempDiv.css({
					'top':(i*MHSchedule.WeekModule.blockSize)+'px',
					'height':MHSchedule.WeekModule.blockSize-1+'px',
					'left':(timeWidth+day*slotWidth)+'px'
				});
			calDiv.append(tempDiv);
		}
	}
	
	// Now, display!
	jQuery('div#calendar_main').append(calDiv);
	
	// And, set the top of the div to 7:00 am
	jQuery('div#calendar_display').scrollTop(7*2*MHSchedule.WeekModule.blockSize);
}

MHSchedule.WeekModule.showEvents = function() {
	for (key in MHSchedule.events){
		MHSchedule.events[key].reposition(); // won't display it if it shouldn't be displayed.
	}
	
	for (var i=0; i<MHSchedule.newEvents.length; ++i ){
		if (MHSchedule.newEvents[i] != null) {
			MHSchedule.newEvents[i].reposition(); // won't display it if it shouldn't be displayed.
		}
	}
}

MHSchedule.WeekModule.newEventHandler = function(event, ui) {
	var x = event.pageX - this.offsetLeft - MHSchedule.WeekModule.timeWidth - 1; // -1 for the time display column's border
	if (x < 0) {
		//alert(x);
		//alert(event.pageX+" "+event.originalTarget.parentNode.offsetLeft+" "+event.originalTarget.offsetLeft);
		return;
	}
	var y = event.pageY - this.offsetTop - 1; // can't seem to get 0, so subtract 1.
	
	var dayOffset = parseInt(x/76)*86400000; // * number of milliseconds in a day
	
	var startTime = new Date(MHSchedule.baseDate.getTime()+dayOffset);
	var topPixels = this.scrollTop + y;
	var totalMinutes = MHSchedule.WeekModule.PixelsToMinutes(topPixels);
	
	startTime.setMinutes((Math.floor(totalMinutes/30))*30);
	
	MHSchedule.newEventOverlay(startTime);
	
	return;
}

MHSchedule.WeekModule.draggedNewUserEventHandler_byDuration = function(event, ui, durationDays, durationHours, durationMinutes) {
	/* Getting the cursor drop location is kind of tricky. We first get the
	 * pageX and pageY position of the cursor. Then, subtract off the X and Y
	 * offsets of the container calendar div.
	 */
	
	var calendarDiv = $('div#calendar_display');
	var calendarDivOffset = calendarDiv.offset();
	var calendarDivX = Math.round(calendarDivOffset.left); // Rounding because we can get floating point values (seriously!)
	var calendarDivY = Math.round(calendarDivOffset.top); // Rounding because we can get floating point values (seriously!)
	
	/* The following pageX and pageY are for the top left corner of the event
	 * that was dropped. To use the cursor's position:
	 *    var pageX = event.pageX;
	 *    var pageY = event.pageY;
	 */
	var pageX = Math.round(ui.offset.left); // Rounding because we can get floating point values (seriously!)
	var pageY = Math.round(ui.offset.top); // Rounding because we can get floating point values (seriously!)
	
	var eventX = pageX-calendarDivX;
	eventX += Math.round((ui.draggable.width()+MHSchedule.WeekModule.eventBorderCompensation)/2);
	var eventY = pageY-calendarDivY + calendarDiv.scrollTop();
	
	// DEBUG:
	try {
		var userID = ui.draggable.attr('userID');
	}
	catch (error) {
		alert('error on trying to get userID.');
		alert(ui.draggable);
		return;
	}
	
	var day = MHSchedule.WeekModule.PixelsToDay(eventX);
	var minutes = MHSchedule.WeekModule.PixelsToMinutes(eventY, 15);
	
	var startDate = new Date(MHSchedule.baseDate);
	startDate.setMinutes(minutes);
	startDate.setDate(startDate.getDate()+day);
	
	// Clean up inputs
	durationDays = parseInt(durationDays, 10);
	durationHours = parseInt(durationHours, 10);
	durationMinutes = parseInt(durationMinutes, 10);
	// 
	
	var endDate = new Date(startDate);
	endDate.setDate(endDate.getDate()+durationDays);
	endDate.setHours(endDate.getHours()+durationHours);
	endDate.setMinutes(endDate.getMinutes()+durationMinutes);
	
	var newEvent = new MHSchedule.ScheduleEventByFields(
				'new'+MHSchedule.newEvents.length.toString(), userID, 0,
				
				startDate.getFullYear(), startDate.getMonth(), startDate.getDate(),
				startDate.getHours(), startDate.getMinutes(),
				
				endDate.getFullYear(), endDate.getMonth(), endDate.getDate(),
				endDate.getHours(), endDate.getMinutes()
				);
	MHSchedule.displaySaveWarning();
	MHSchedule.newEvents.push(newEvent);
	newEvent.display();
}

MHSchedule.WeekModule.draggedNewUserEventHandler_byTime = function(event, ui, startHours, startMinutes, endHours, endMinutes) {
	/* Getting the cursor drop location is kind of tricky. We first get the
	 * pageX and pageY position of the cursor. Then, subtract off the X and Y
	 * offsets of the container calendar div.
	 */
	
	var calendarDiv = $('div#calendar_display');
	var calendarDivOffset = calendarDiv.offset();
	var calendarDivX = Math.round(calendarDivOffset.left); // Rounding because we can get floating point values (seriously!)
	var calendarDivY = Math.round(calendarDivOffset.top); // Rounding because we can get floating point values (seriously!)
	
	/* The following pageX and pageY are for the top left corner of the event
	 * that was dropped. To use the cursor's position:
	 *    var pageX = event.pageX;
	 *    var pageY = event.pageY;
	 */
	var pageX = Math.round(ui.offset.left); // Rounding because we can get floating point values (seriously!)
	var pageY = Math.round(ui.offset.top); // Rounding because we can get floating point values (seriously!)
	
	var eventX = pageX-calendarDivX;
	eventX += Math.round((ui.draggable.width()+MHSchedule.WeekModule.eventBorderCompensation)/2);
	var eventY = pageY-calendarDivY + calendarDiv.scrollTop();
	
	// DEBUG:
	try {
		var userID = ui.draggable.attr('userID');
	}
	catch (error) {
		alert('error on trying to get userID.');
		alert(ui.draggable);
		return;
	}
	
	var day = MHSchedule.WeekModule.PixelsToDay(eventX);
	var minutes = MHSchedule.WeekModule.PixelsToMinutes(eventY, 15);
	
	var startDate = new Date(MHSchedule.baseDate);
	startDate.setMinutes(minutes);
	startDate.setDate(startDate.getDate()+day);
	startDate.setHours(startHours);
	startDate.setMinutes(startMinutes);
	
	var endDate = new Date(startDate);
	// Check to see if the end time is before the start time. If it is, then
	// build this end time for the day after.
	if ((startHours*60)+startMinutes >= (endHours*60)+endMinutes) {
		endDate.setDate(endDate.getDate()+1);
	}
	endDate.setHours(endHours);
	endDate.setMinutes(endMinutes);
	
	var newEvent = new MHSchedule.ScheduleEventByFields(
				'new'+MHSchedule.newEvents.length.toString(), userID, 0,
				
				startDate.getFullYear(), startDate.getMonth(), startDate.getDate(),
				startDate.getHours(), startDate.getMinutes(),
				
				endDate.getFullYear(), endDate.getMonth(), endDate.getDate(),
				endDate.getHours(), endDate.getMinutes()
				);
	MHSchedule.displaySaveWarning();
	MHSchedule.newEvents.push(newEvent);
	newEvent.display();
}


MHSchedule.WeekModule.dragEventHandler = function(event, ui) {
	event.stopPropagation();
	
	var eventDiv = $(this);
	var position = eventDiv.position();
	var scheduleEvent = MHSchedule.findEventByDiv(event.target);
	//var eventID = parseInt(scheduleEvent.target.getAttribute('id').substring(5));
	//var scheduleEvent = MHSchedule.events[eventID];
	
	var eventDuration = scheduleEvent.endDate.getTime() - scheduleEvent.startDate.getTime();
	
	// Check to see if this was a valid move
	
	// First, check to see if the top of the div goes off the bottom of the schedule.
	if (position.top+document.getElementById('calendar_display').scrollTop > MHSchedule.WeekModule.totalHeight) {
		scheduleEvent.reposition();
		scheduleEvent.updateEventDivText();
		return;
	}
	// Next, check to see if the bottom of the div goes off the top of the schedule.
	if ((position.top+eventDiv.height()) < 0) {
		scheduleEvent.reposition();
		scheduleEvent.updateEventDivText();
		return;
	}
	// Next, check to see if the top left of the div goes off the table to the left.
	if (position.left < MHSchedule.WeekModule.timeWidthOffset) {
		scheduleEvent.reposition();
		scheduleEvent.updateEventDivText();
		return;
	}
	// Last, check to see if the top left of the div goes off the table to the right.
	if (position.left > MHSchedule.WeekModule.timeWidth+(6*MHSchedule.WeekModule.slotWidth)) {
	//if (position.left > 550) {
		scheduleEvent.reposition();
		scheduleEvent.updateEventDivText();
		return;
	}
	// Okay, we have a valid move.
	MHSchedule.displaySaveWarning();
	++MHSchedule.undoLevels;
	scheduleEvent.changeFlag = true;
	
	// Back up the old schedule data for undo.
	scheduleEvent.undoStartDate = new Date(scheduleEvent.startDate.getTime());
	scheduleEvent.undoEndDate = new Date(scheduleEvent.endDate.getTime());
	
	var topPosition = (position.top+document.getElementById('calendar_display').scrollTop)
	//alert('Debug point 1: '+topPosition);
	var oldStartTimeInMinutes = (scheduleEvent.startDate.getHours()*60+scheduleEvent.startDate.getMinutes());
	
	// Start times on drag should be in 15 minute increments, just as they are
	// for new events on click. This calculation is based on the 30-minute block
	// that the grid is drawn using (in order to minimize rounding errors).
	var newStartTimeInMinutes = MHSchedule.WeekModule.PixelsToMinutes(topPosition, 15);
	//alert('Debug point 2a: '+newStartTimeInMinutes);
	//alert('Debug point 2b: '+oldStartTimeInMinutes);
	//alert('Debug point 2c: '+topPosition);
	var minutesDelta = newStartTimeInMinutes - oldStartTimeInMinutes;
	//alert('Debug point 3: '+minutesDelta);
	var multiDaySegment = +(eventDiv.attr('segment')); // typeconvert into an integer!
	//alert('Debug point 4: '+multiDaySegment);
	if (multiDaySegment > 0) {
		//minutesDelta += eventDiv.attr('segment')*1440; // add number of days
		var dayOffset = eventDiv.attr('segment');
		var newMinutesDelta = newStartTimeInMinutes;
		minutesDelta = newMinutesDelta;
		//alert('Debug point 6: '+minutesDelta);
		multiDaySegment = +multiDaySegment; // typeconvert into an integer!
	}
	var newDay = Math.round((position.left-MHSchedule.WeekModule.timeWidth)/MHSchedule.WeekModule.slotWidth);
	newDay = Math.round(newDay);
	//alert('Debug point 7a: '+newDay);
	
	var eventStartCalendarDay = (scheduleEvent.startDate.getDay()-MHSchedule.baseDate.getDay()+7)%7;
	var divCalendarDay = (eventStartCalendarDay+multiDaySegment);//%7;
	var oldDay = Math.round(((scheduleEvent.startDate.getDay()-MHSchedule.baseDate.getDay()+multiDaySegment)+7)%7);
	//alert('Debug point 9a: '+oldDay);
	var dayDelta = newDay-oldDay;
	
	//alert('Debug point 10a-1: '+scheduleEvent.startDate);
	//alert('Debug point 10a-2: '+minutesDelta);
	//alert('Debug point 10a-3: '+(dayDelta*1440));
	scheduleEvent.startDate.setMinutes(scheduleEvent.startDate.getMinutes()+minutesDelta+(dayDelta*1440));
	scheduleEvent.endDate.setMinutes(scheduleEvent.endDate.getMinutes()+minutesDelta+(dayDelta*1440));
	//alert('Debug point 10b: '+scheduleEvent.startDate);
	
	scheduleEvent.reposition();
	scheduleEvent.updateEventDivText();
	
	while (scheduleEvent.undoJQueryDiv.length > 0) {
		scheduleEvent.undoJQueryDiv.pop().remove();
	}
	MHSchedule.displayEventDivUndo(scheduleEvent, position.top, position.left);
}


MHSchedule.WeekModule.RepositionEvent = function(event) {
	/* General strategy:
	 * 
	 * 1. First, check to see if this event should be displayed.
	 * 2. Next, check to see if the first div should be displayed.
	 * 3. For each remaining div (if it's a multi-day event), check to see
	 *    if it should be displayed. If so, great. If not, don't.
	 */
	
	// Is this event deleted?
	if (event.deleteFlag) {
		// Remove all divs it may have.
		while(event.jQueryDiv.length > 0) {
			event.jQueryDiv.pop().remove();
		}
		return;
	}
	
	
	/* Relevant variables:
	 * 
	 * MHSchedule.baseDate (provided by MHSchedule) - calendar earliest displayed date
	 * MHSchedule.endDate - calendar last displayed date + 1 minute
	 * currentDisplayDate - The div being displayed next shall be for this date
	 */
	
	var currentDisplayDate = new Date(event.startDate.getTime());
	currentDisplayDate.setHours(0,0,0,0); // zero out hours, minutes, seconds, milliseconds
	
	// If the start date is after the displayed date range, or if the
	// end date is before the displayed date range. This should be
	// sufficient to avoid all cases where events aren't displayed.
	if (event.startDate >= MHSchedule.endDate || event.endDate <= MHSchedule.baseDate) {
		//alert('hiding event startDate '+event.startDate.toString()+' event.endDate '+event.endDate.toString());
		// Hide this event if it's showing.
		while(event.jQueryDiv.length > 0) {
			event.jQueryDiv.pop().remove();
		}
		return;
	}
	
	/* four cases for an event:
	 * 1. Entirely contained within the calendar
	 * 		startDate > baseDate && startDate < endDate &&
	 * 		endDate > baseDate && endDate < endDate
	 *    Base behavior.
	 * 2. Spans over the start of the week
	 * 		startDate < baseDate &&
	 * 		endDate > baseDate && endDate < endDate
	 *    This event is when an event spans over the start of the week from the
	 *    previous week. (that is, one or more div segments belong in the
	 *    previous week) To handle this case, calculate how many divs were
	 *    skipped, and pick up from there, at the start of the week.
	 * 3. Spans over the end of the week
	 * 		startDate > baseDate && startDate < endDate &&
	 * 		endDate > endDate
	 *    Just operate normally, until the end of the week is reached. Then end
	 *    execution.
	 * 4. Spans over the full week
	 * 		startDate < baseDate
	 * 		endDate > endDate
	 *    This will automatically be handled by cases 2 and 3.
	 */
	
	// First, remove all divs related to this event. This simplifies the
	// problem in that we don't have to worry about animating/moving existing
	// divs as well as creating them. Instead, we just have to worry about
	// creating them.
	while(event.jQueryDiv.length) {
		var temp = event.jQueryDiv.pop();
		temp.animate({
			opacity: 0
		}, 500);
		temp.remove();
	}
	
	// This function keeps track of event duration in number of pixels. By
	// keeping track of how many pixels we've displayed, we can get a grasp of
	// how many pixels remain (with regard to displaying events that span days).
	//var totalMinutes = ((event.endDate.getTime()-event.startDate.getTime())/60000); // 60000 is # of milliseconds in a minute
	//var remainingYPixels = MHSchedule.WeekModule.MinutesToPixels(totalMinutes);
	
	var startPixels = MHSchedule.WeekModule.DateToWeekPixels(event.startDate);
	var endPixels = MHSchedule.WeekModule.DateToWeekPixels(event.endDate);
	var remainingYPixels = endPixels-startPixels;
	
	// Keeps track of which div we're currently displaying, with relation to the
	// event. This is used for a div attribute, as well as its ID.
	var currentDiv = 0;
	
	// Book keeping for event case #3. This value keeps track of which day we're
	// currently displaying. We'll know to stop because currentDay will equal
	// MHSchedule.endDate.
	//    While this is being set up, we're going to use the data gleaned here
	// to set up the cssLeft value -- this is what we're going to use to keep
	// track of the left position for each of these event divs as we go from day
	// to day.
	var currentDivDay = new Date(event.startDate.getTime());
	currentDivDay.setHours(0,0,0,0); // Get rid of time -- we only care about the date.
	
	// Keeps track of how far left the event should be positioned. This directly
	// corresponds to which day we're currently displaying the event div for.
	var cssLeft = MHSchedule.WeekModule.timeWidthOffset;
	
	// Handle event case #2:
	if (event.startDate < MHSchedule.baseDate) {
		// Don't worry about how many pixels need to be displayed.
		// DateToWeekPixels will correctly give us the number of pixels.
		
		//currentDiv += Math.ceil(previousWeekPixels/MHSchedule.WeekModule.totalHeight);
		currentDiv += 1;
		currentDivDay.setDate(currentDivDay.getDate()+currentDiv);
	}
	else {
		// Set up cssLeft.
		var dateDelta = MHSchedule.DaysDifference(MHSchedule.baseDate, currentDivDay);
		cssLeft += dateDelta*MHSchedule.WeekModule.slotWidth;
	}
	
	while(remainingYPixels) {
		var eventDiv = $(document.createElement('div'));
		eventDiv.attr('id', 'event'+event.id);
		eventDiv.attr('segment', currentDiv);
		eventDiv.addClass('schedule_event');
		if (event.type == 1) {
			eventDiv.addClass('schedule_event_administrative');
		}
		else {
			eventDiv.addClass('schedule_event_medical');
		}
		
		// Now, onto CSS.
		if (!currentDiv) {
			// This is not the first div, so it should always start at the top
			// of the calendar.
			var topInMinutes = (event.startDate.getHours()*60)+event.startDate.getMinutes();
			var cssTop = MHSchedule.WeekModule.MinutesToPixels(topInMinutes);
		}
		else {
			var cssTop = 0;
		}
		var cssHeight = remainingYPixels;
		if (cssHeight+cssTop > MHSchedule.WeekModule.totalHeight) {
			cssHeight = MHSchedule.WeekModule.totalHeight-cssTop;
		}
		remainingYPixels -= cssHeight;
		cssHeight -= MHSchedule.WeekModule.eventBorderCompensation;
		
		eventDiv.css({
				'background-color': MHSchedule.userColorsAssigned[event.userID],
				
				// Setting position here because Chrome and Safari don't
				// seem to get this attribute from the stylesheet.
				'position': 'absolute',
				'top': cssTop,
				'height': cssHeight,
				'left': cssLeft,
				'width': MHSchedule.WeekModule.slotWidth-MHSchedule.WeekModule.eventBorderCompensation-1 // -1 to compensate for the vertical grid line
			});
		
		// Set up event handlers
		eventDiv.click(MHSchedule.editEvent);
		eventDiv.draggable({
					distance: 5,
					scroll: false,
					//containment: 'parent',
					grid: [MHSchedule.WeekModule.slotWidth,1],
					stop: MHSchedule.currentModule.dragEventHandler
					// The following is disabled. It looks like the div text doesn't
					// automagically update during the drag.
					// drag: updateEventDivText_EventHandler,
				});
		
		// Update the div to reflect the new div. Then add it to the DOM.
		event.jQueryDiv.push(eventDiv);
		eventDiv.hide();
		calendarDiv.append(eventDiv);
		eventDiv.show();
		
		// Move on to the next day
		++currentDiv;
		currentDivDay.setDate(currentDivDay.getDate()+1);
		cssLeft += MHSchedule.WeekModule.slotWidth;
		
		// Check for and resolve event case #3 -- stop displaying divs.
		if (currentDivDay >= MHSchedule.endDate) {
			remainingYPixels = 0;
		}
	}
	
	event.updateEventDivText();
}


MHSchedule.WeekModule.MinutesToPixels = function(minutes) {
	var num30MinBlocks = Math.floor(minutes/30);
	var remainderMins = minutes%30;
	return(num30MinBlocks*MHSchedule.WeekModule.blockSize + Math.round(remainderMins*MHSchedule.WeekModule.minPerPixel));
}
MHSchedule.WeekModule.PixelsToMinutes = function(pixels, round) {
	var negative = pixels < 0;
	pixels = Math.abs(pixels);
	var num30MinBlocks = Math.floor(pixels/MHSchedule.WeekModule.blockSize);
	var remainderPixels = pixels%MHSchedule.WeekModule.blockSize;
	var remainderMinutes = Math.round(remainderPixels/MHSchedule.WeekModule.minPerPixel);

	if (round) {
		// If this is given, we're going to round to the requested # of mins.
		var remainderMinutes = Math.floor(remainderMinutes/round) + Math.floor((remainderMinutes%round)/(round/2));
		remainderMinutes *= round;
	}
	
	var returnVal = num30MinBlocks*30 + remainderMinutes;
	if (negative) {
		returnVal *= -1;
	}
	return(returnVal);
}
MHSchedule.WeekModule.DayToPixels = function(day) {
	return(MHSchedule.WeekModule.timeWidth + day*MHSchedule.WeekModule.slotWidth);
}
MHSchedule.WeekModule.PixelsToDay = function(pixels) {
	var dayPixels = pixels - MHSchedule.WeekModule.timeWidth;
	return(Math.floor(dayPixels/MHSchedule.WeekModule.slotWidth));
}
MHSchedule.WeekModule.DateToDayPixels = function(date) {
	var hours = date.getHours();
	var minutes = date.getMinutes();
	
	var num30MinBlocks = hours*2+Math.floor(minutes/30);
	var remainderMinutes = minutes%30;
	var remainderPixels = Math.round(remainderMinutes/MHSchedule.WeekModule.minPerPixel);
}
MHSchedule.WeekModule.DateToWeekPixels = function(date) {
	if (date <= MHSchedule.baseDate) {return 0;}
	if (date >= MHSchedule.endDate) {return 7*MHSchedule.WeekModule.totalHeight;}

	// using MHSchedule.baseDate
	var strippedDate = new Date(date);
	strippedDate.setHours(0,0,0,0);
	var days = MHSchedule.DaysDifference(MHSchedule.baseDate, strippedDate);
	var hours = date.getHours();
	var minutes = date.getMinutes();
	
	var num30MinBlocks = hours*2+Math.floor(minutes/30);
	var remainderMinutes = minutes%30;
	
	var dayPixels = days*MHSchedule.WeekModule.totalHeight;
	var blockPixels = num30MinBlocks*MHSchedule.WeekModule.blockSize;
	var remainderPixels = Math.round(remainderMinutes*MHSchedule.WeekModule.minPerPixel);
	
	return dayPixels + blockPixels + remainderPixels;
}
