
/* Schedule event object
 */
MHSchedule.ScheduleEvent = function(id, userID, eventType, startDate, endDate, checkString) {
	// 'id' is the Django-schedule event ID.
	this.id = id
	
	this.userID = userID;
	this.primaryFlag = true;
	
	this.startDate = new Date(startDate);
	this.endDate = new Date(endDate);
	
	/* type is 0 for medical on-calls, and type 1 is for administrative on-calls. */
	this.type = eventType;
	
	// Undo Data
	this.undoStartDate = null;
	this.undoEndDate = null;
	this.undoJQueryDiv = [];
	
	this.jQueryDiv = [];
	
	this.newFlag = false; // True if this event is new -- if it's not yet on the server.
	this.deleteFlag = false; // Set to true if this is on the slate to be deleted.
	this.changeFlag = false; // Set to true if this event has been changed and needs to be sent to the server.
	
	this.model = 'Scheduler.evententry';
	
	this.display = function() {
		// This is an obsolete function. Use this.reposition instead.
		return this.reposition();
	}
	
	if (!checkString) {
		this.checkString = MHSchedule.ajaxUtils.randomString();
	}
	else {
		this.checkString = checkString;
	}
	
	this.changeEventType = function(newType) {
		this.type = newType;
		var types = ['schedule_event_medical', 'schedule_event_administrative'];
		for (var i = 0; i < this.jQueryDiv.length; i++) {
			this.jQueryDiv[i].removeClass('schedule_event_administrative');
			this.jQueryDiv[i].removeClass('schedule_event_medical');
			this.jQueryDiv[i].addClass(types[this.type]);
		}
	}
	
	this.changeDates = function(newStartDate, newEndDate) {
		this.startDate = newStartDate;
		this.endDate = newEndDate;
		this.reposition();
		this.updateEventDivText();
	}
	
	this.reposition = function() {
		MHSchedule.currentModule.RepositionEvent(this);
	}
	
	this.updateEventDivText = function() {
		var AMPM = ' am';
		var startHour = this.startDate.getHours();
		if (startHour > 11) {
			AMPM = ' pm';
			startHour = startHour-12;
		}
		if (startHour == 0) {
			startHour = 12;
		}
		var startMinute = this.startDate.getMinutes()
		if (startMinute < 10) {
			startMinute = '0'+startMinute;
		}
		var startTime = startHour+":"+startMinute+AMPM;
		
		AMPM = ' am';
		var endHour = this.endDate.getHours();
		if (endHour > 11) {
			AMPM = ' pm';
			endHour = endHour-12;
		}
		if (endHour == 0) {
			endHour = 12;
		}
		var endMinute = this.endDate.getMinutes()
		if (endMinute < 10) {
			endMinute = '0'+endMinute;
		}
		var endTime = endHour+":"+endMinute+AMPM;
		
		// Add the date if this is a multi-day event.
		// Update: Just display the dates always.
		//if (this.jQueryDiv.length > 1) {
		startTime = startTime+'<br />'+(this.startDate.getMonth()+1)+'/'+this.startDate.getDate();
		endTime = endTime+'<br />'+(this.endDate.getMonth()+1)+'/'+this.endDate.getDate()+'<br />';

		//180 color and member order Chen Hu
		if(MHSchedule.availableUsers[this.userID]!=null)
		{
			//console.log(this.userID) ;
			//console.dir(MHSchedule.availableUsers) ;
			//console.dir(MHSchedule.availableUsers[this.userID]) ;
			//console.trace();
			userFullName = MHSchedule.availableUsers[this.userID]['first_name']+' '+
			MHSchedule.availableUsers[this.userID]['last_name'];
			
			for (var i = 0; i < this.jQueryDiv.length; i++) {
				//alert('foo');
				this.jQueryDiv[i].html('<b>'+userFullName+'</b><br /><i>'+startTime+'</i><br />to<br /><i>'+endTime+'</i>');
				//$('div#footer').append(undoDiv);
			}
		}
	}


	this.undoMove = function() {
		this.changeDates(new Date(this.undoStartDate.getTime()),
							new Date(this.undoEndDate.getTime()));
		
		this.undoCleanup();
		
		--MHSchedule.undoLevels;
		if (MHSchedule.undoLevels == 0) {
			$('#calendar_save_warning').hide(500);
		}
	}
	this.undoCleanup = function() {
		// Cleans up after the this undo div is either hidden (after timeout) or
		// the undo link is clicked.
		
		while(this.undoJQueryDiv.length > 0) {
			this.undoJQueryDiv.pop().remove();
		}
	
		this.undoStartDate = null;
		this.undoEndDate = null;
	}
	
	this.delEvent = function() {
		// First, run undoCleanup to keep the DOM from getting too cluttered.
		this.undoCleanup();
		// Next, undisplay this item.
		while(this.jQueryDiv.length > 0) {
			div = this.jQueryDiv.pop();
			div.hide(200);
			div.remove();
		}
		// Lastly, flag the event for removal.
		this.deleteFlag = true;
		this.changeFlag = true;
	}
}

MHSchedule.ScheduleEventByFields = function(id, userID, eventType, 
			startYear, startMonth, startDay, startHour, startMinute,
			endYear, endMonth, endDay, endHour, endMinute, checkString) {
	startDate = new Date(startYear, startMonth, startDay, startHour, startMinute);
	endDate = new Date(endYear, endMonth, endDay, endHour, endMinute);
	return(new MHSchedule.ScheduleEvent(id, userID, eventType, startDate, endDate, checkString));
}

MHSchedule.clearAllEvents = function() {
	for (key in MHSchedule.events) {
		while(MHSchedule.events[key].jQueryDiv.length > 0) {
			MHSchedule.events[key].jQueryDiv.pop().remove();
		}
	}
	arLen=MHSchedule.newEvents.length;
	for (var i=0; i<arLen; ++i ){
		if (MHSchedule.newEvents[i] != null) {
			while(MHSchedule.newEvents[i].jQueryDiv.length > 0) {
				MHSchedule.newEvents[i].jQueryDiv.pop().remove();
			}
		}
	}
}
 
MHSchedule.displayEventDivUndo = function(event, schedTop, schedLeft) {
	var undoDiv = $(document.createElement('div'));
	undoDiv.addClass('scheduleEvent_undoDiv');
	undoDiv.attr('id', 'scheduleEvent_undoDiv_'+event.id);
	undoDiv.attr('event', event.id);
	
	//undoDiv.html('<a href="javascript:eventUndoMove(\''+event.id+'\');">undo</a>');
	
	var undoLink = $(document.createElement('a'));
	undoLink.addClass('close');
	undoLink.html('undo');
	undoLink.attr('event', event.id);
	undoLink.click(MHSchedule.eventUndoMove);
	
	undoDiv.append(undoLink);
	
	
	// TODO: The undo needs to be placed someplace. It should be placed on each.
	for (var i = 0; i < event.jQueryDiv.length; i++) {
		event.jQueryDiv[i].append(undoDiv);
		//$('div#footer').append(undoDiv);
	}
	
	event.undoJQueryDiv.push(undoDiv);
	
	undoDiv.show(500);
}

MHSchedule.eventUndoMove = function(event) {
	event.stopPropagation();
	event = MHSchedule.findEventByID($(this).attr('event'));
	
	event.undoMove();
}

/*
*	2011-7-28 
*	refresh #179  refresh
*/
function refresh(){
	MHSchedule.clearAllEvents();
	MHSchedule.events = {};
	MHSchedule.availableUsers = {};
	MHSchedule.userColorsAssigned = {};
	MHSchedule.userColorsAssignedCounter = 0;
	MHSchedule.ajax.eventDatesCached = [];
	MHSchedule.getEvents(MHSchedule.baseDate, MHSchedule.endDate);
	MHSchedule.refreshCallGroupMembers();
}