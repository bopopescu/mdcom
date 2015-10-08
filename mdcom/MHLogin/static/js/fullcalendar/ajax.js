var MHSchedule = {
	DAYTIME_FORMAT: 'yyyy-MM-dd HH:mm:ss',
	DAYTIME_FORMAT_TITLE: 'MM/dd hh:mm tt',
	DAYTIME_FORMAT_MONTH_TITLE: 'HH:mm',
	userColorsAvailable : [
		'#8accd9', '#9a81ee', '#e187be',
		'#dcd069', '#88e859', '#f2a948',
		'#d1d1d1', '#6f97f3', '#ff6b6b',
		'#c5e084', '#ba9976', '#33ca3a',
		'#eec19c', '#8d30ce', '#d40000'
	],
	eventTypes: ['schedule_event_medical', 'schedule_event_administrative'],	
	availableUsers: false,
	userColorsAssigned: false,
	undoSize:0,
	redoSize:0,
	lastView: {},
	needSaveLastView: false
};

$(function(){
	// First, get the list of available members.
	MHSchedule.callGroup.refreshCallGroupMembers();	
	
	// Second, get events and add fullCalenar support.
	MHSchedule.fullcalendar.initCalendar();
	
	/*
	$('#downloadPDFDialog').overlay({
		top: 'center',
		left: 'center',
		mask: {
			color: '#111',
			loadSpeed: 200,
			opacity: 0.7
		},
		fixed: false, // add by xlin to fix in IE
		closeOnClick: true
	});*/
	
	
	var currentYear = (new Date).getFullYear();
	$('#calendar2 .year').text(currentYear);
	var month = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];
	$('#calendar2 .content td').each(function(){
		var currentMonth = (new Date()).getMonth();
		if(month[currentMonth]==$(this).find('span').text()){
			$(this).addClass('currentMonth');
		}
	});
	
	$('#calendar2 .prev').click(function(){
		MHSchedule.pdf.clickPrevYear(currentYear);
	});
	
	$('#calendar2 .next').click(function(){
		MHSchedule.pdf.clickNextYear(currentYear);
	});
	
	$('#calendar2 td').click(function(){
		$('#calendar2 td').removeClass('currentMonth');
		$(this).addClass('currentMonth');
		MHSchedule.pdf.downloadPDF();
	});
	
	$('.newOnCall .help_icon').hover(function(){
		$('#note_help').removeClass('hidden');
	},function(){
		$('#note_help').addClass('hidden');
	});
});

/**************************************************** CallGroupMembers ************************************************/
MHSchedule.callGroup = {};
/* initialize the callgroupmembers  */
MHSchedule.callGroup.refreshCallGroupMembers = function() {
	$.ajax({
		url: '../AJAX/getMembers/',
		type: 'POST',
		async: false,
		success: function(data, textStatus, httpRequest) {
			// Test for success
			if (textStatus == 'success') {
				// Clear the current availableUsers list and color assignments.
				MHSchedule.availableUsers = {};
				MHSchedule.userColorsAssigned = {};
				for (var idx=0; idx<data.length; idx++) {
					user = data[idx];
					//#180 Color and user older Chen Hu 
					MHSchedule.availableUsers[user[0]] = {
						id: user[0],
						first_name: user[1],
						last_name: user[2],
						fullname: user[3],
						index:idx
					};
					MHSchedule.userColorsAssigned[user[0]] = MHSchedule.userColorsAvailable[idx%MHSchedule.userColorsAvailable.length];
				}
				MHSchedule.callGroup.displayCallGroupMembers();
			}
		}, // end success
		error: function(httpRequest, textStatus, errorThrown) {
			alert('An error occurred getting a list of call group users.');
			$('div#errorDebug').html(httpRequest.responseText);
			return;
		}
	});	
};

/*
 * new method for showing call group members 
 *  modify by xlin 2011-11-28
 */
MHSchedule.callGroup.displayCallGroupMembers = function() {
	var html = "";
	var color_idx = 0;
	var UserIdArray = Array();
	//180 color and member order Chen Hu
	for(var id in MHSchedule.availableUsers){
		UserIdArray[MHSchedule.availableUsers[id].index] = id;
	}
	var userCount = UserIdArray.length;
	for (var i=0; i<userCount; i++) {
		var id = UserIdArray[i];
		var color = MHSchedule.userColorsAssigned[id];
		var name = MHSchedule.availableUsers[id]['fullname'];
		if(userCount > 15 && !isIPad()){
			html += '<div class="item2 calendar_user" userID="' + id + '" title="' + name + '">';
			html += '	<div class="color2" style="';
		}else{
			html += '<div class="item calendar_user" userID="' + id + '" title="' + name + '">';
			html += '	<div class="color" style="';
		}
		html += ' 		border:1px solid '+ color + ';';
		html += '		background:'+ color + ';';
		html += '	">';
		
		if(userCount > 15){
			if(name.length > 13){
				name = name.slice(0,11) + '...';
			}
		}else{
			if(name.length > 21){
				name = name.slice(0,18) + '...';
			}
		}
		html += '<span>'+name+'</span>';
		html += '<div class="icon_move"></div>';
		html += '	</div>';
		html += '</div>';
		++color_idx;
	}	
	html += '<div class="clear"></div>';
	var userContainer = $("#calendar_available_users");
	if(userCount > 15){
		userContainer.addClass('usersOverflow');
	}else{
		userContainer.addClass('usersNotOverflow');
	}
	userContainer.html(html);
	
	// Event Handler
	$('.calendar_user', userContainer).each(function() {
		var jObj = $(this);
		var userID = jObj.attr("userID");
		var eventObject = {
			userID: userID
		};
		jObj.data('eventObject', eventObject);
		jObj.css({"cursor": Constant.OpenHandCursor})
			.mousedown(function(){
				$(this).css({"cursor": Constant.ClosedHandCursor});
			}).mouseup(function(){
				$(this).css({"cursor": Constant.OpenHandCursor});
			})
			.draggable({
				zIndex: 999,
				revert: 'invalid',
				revertDuration:0,
				scroll:false,
				helper: 'clone',	
				containment:'#content_div',
				stop: function(event, ui) {
					$('#calendar_available_users .calendar_user').css({"cursor": Constant.OpenHandCursor});	
				}
			});
	});
};

/******************************************************** fullcalendar ************************************************/
MHSchedule.fullcalendar = {};
/* initialize the fullcalendar */
MHSchedule.fullcalendar.initCalendar = function() {
	
	var view = MHSchedule.schedule.getViewInfo();
	
	var agenda = '';
	var axisFormat = '';
	if(Constant.TIME_SETTING==1){
		agenda = 'HH:mm{-HH:mm}';
		axisFormat = 'HH(:mm)';
	}else{
		agenda = 'hh:mmtt{-hh:mmtt}';
		axisFormat = 'h(:mm)tt';
	}
	var calendar = $('#calendar').fullCalendar($.extend(view, {
		header: {
			left: 'prevYear,prev,next,nextYear today',
			center: 'title',
			right: 'month,agendaWeek,agendaDay undo,redo'
		},

		buttonText: {
			today: MESSAGE.SCHEDULE_FULLCALENDAR_TODAY,
			month: MESSAGE.SCHEDULE_FULLCALENDAR_MONTH,
			week: MESSAGE.SCHEDULE_FULLCALENDAR_WEEK,
			day: MESSAGE.SCHEDULE_FULLCALENDAR_DAY,
			undo: MESSAGE.SCHEDULE_FULLCALENDAR_UNDO,
			redo: MESSAGE.SCHEDULE_FULLCALENDAR_REDO
		},
		monthNames: MESSAGE.SCHEDULE_FULLCALENDARL_MONTH_NAMES,
		monthNamesShort: MESSAGE.SCHEDULE_FULLCALENDARL_MONTH_NAMES_SHORT,
		dayNames: MESSAGE.SCHEDULE_FULLCALENDARL_DAY_NAMES,
		dayNamesShort: MESSAGE.SCHEDULE_FULLCALENDARL_DAY_NAMES_SHORT,

		allDaySlot: false,
		height:670,
		slotMinutes: 15,
		timeFormat: {
			agenda: agenda
		},
		axisFormat:axisFormat,
		
		editable: true,
		select: function(start, end, allDay) {
			if(!MHSchedule.schedule.checkCurrentDate(MESSAGE.SCHEDULE_ERROR_EARLIER_THAN_TODAY1, [start])){
				calendar.fullCalendar('unselect');
				return false;
			}else{
				var savedEndDate = new Date(end);
				if ('month'==$('#calendar').fullCalendar('getView').name) {
					var duration = MHSchedule.schedule.getDuration(start, savedEndDate);
					if (duration.valid) {
						start = duration.start;
						savedEndDate = duration.end;
					} else {
						calendar.fullCalendar('unselect');
						return false;
					}	
//					savedEndDate.setDate(end.getDate()+1);
//					savedEndDate.setSeconds(end.getSeconds()-1);						
				}
				var calEvent = {
					start: start,
					end: savedEndDate,
					allDay: false
				};
				MHSchedule.schedule.displayEventEditor(
					calEvent, 
					true,
					function(){
						$('#calendar').fullCalendar('unselect');
					});
			}
		},
		selectable: true,
		selectHelper: true,
		unselectCancel: true,	
		forceDayClick: true,
		dayClick: function(date, allDay, jsEvent, view){
			var startDate = new Date(date);
			var endDate = new Date(date);			
			if(!MHSchedule.schedule.checkCurrentDate(MESSAGE.SCHEDULE_ERROR_EARLIER_THAN_TODAY1, [date])){
				return false;
			}
			
			if ('month'==$('#calendar').fullCalendar('getView').name) {
				var duration = MHSchedule.schedule.getDuration(date);
				if (duration.valid) {
					startDate = duration.start;
					endDate = duration.end;
				} else {
					return false;
				}				
			} else {
				endDate.setHours(endDate.getHours()+8);
			}		
			var calEvent = {
				start: startDate,
				end: endDate,
				allDay: false
			};
			MHSchedule.schedule.displayEventEditor(calEvent, true);
		},
		undo: function() {
			MHSchedule.schedule.undo(this);
		},
		redo: function() {
			MHSchedule.schedule.redo(this);
		},
//		dayDoubleClickEnable: true,
//		dayDoubleClick: function(date, allDay, jsEvent, view){
//			var startDate = date;
//			var endDate = new Date(date);
//			endDate.setHours(endDate.getHours()+8);
//			
//			if(startDate < new Date()){
//				alert(MESSAGE.SCHEDULE_ERROR_EARLIER_THAN_TODAY1);
//				return false;
//			}
//			
//			var calEvent = {
//				start: startDate,
//				end: endDate,
//				allDay: false
//			};
//			MHSchedule.schedule.displayEventEditor(calEvent, true);
//		},				
		droppable: true, // this allows things to be dropped onto the calendar !!!		
		drop: function(date, allDay) { // this function is called when something is dropped
			if(!MHSchedule.schedule.checkCurrentDate(MESSAGE.SCHEDULE_ERROR_EARLIER_THAN_TODAY1, [date])){
				return false;
			}
			var duration = MHSchedule.schedule.getDuration(date);
			if (duration.valid) {
				var originalEventObject = $(this).data('eventObject');
				var calEvent = {
					start: duration.start,
					end: duration.end,
					allDay: false
				};
				calEvent = $.extend(calEvent, originalEventObject);
				MHSchedule.schedule.showConfirmDialog(calEvent, true);
				//MHSchedule.schedule.saveSchedule(calEvent, true);
//				MHSchedule.schedule.displayEventEditor(calEvent, true);				
			}
		},
		eventClick: function(calEvent, jsEvent, view){ //click one event
			if(typeof calEvent.editable !='undefined' && !calEvent.editable){
				return false;
			}
			$(".fc-event-inner").removeClass("fc-event-select");
			$(this).children().addClass('fc-event-select');
			if(MHSchedule.schedule.checkCurrentDate(MESSAGE.SCHEDULE_ERROR_EARLIER_THAN_TODAY2, [calEvent.start])){
				MHSchedule.schedule.displayEventEditor(calEvent);
			}
		},
//		eventDoubleClick: function(calEvent, jsEvent, view){
//			if(calEvent.start < new Date()){
//				alert(MESSAGE.SCHEDULE_ERROR_EARLIER_THAN_TODAY2);
//			}else{
//				MHSchedule.schedule.displayEventEditor(calEvent);
//			}			
//		},
		eventDragStart: function( calEvent, jsEvent, ui, view ) {
			$(this).css({"cursor": Constant.ClosedHandCursor});
		},
		eventDragStop: function( calEvent, jsEvent, ui, view ) {
			$(this).css({"cursor": ""});
		},		
		eventDrop: function(calEvent, dayDelta, minuteDelta, allDay, revertFunc, jsEvent, ui, view){
			var oldEvent = calEvent.oldEvent;
			if(!MHSchedule.schedule.checkCurrentDate(MESSAGE.SCHEDULE_ERROR_EARLIER_THAN_TODAY3, [calEvent.start, oldEvent.start])){
				revertFunc();
			}else{
				MHSchedule.schedule.showConfirmDialog(calEvent, false, revertFunc);
				//MHSchedule.schedule.saveSchedule(calEvent,false);	
			}
		},
		eventResize: function(calEvent, dayDelta, minuteDelta, revertFunc, jsEvent, ui, view){
			if(!MHSchedule.schedule.checkCurrentDate(MESSAGE.SCHEDULE_ERROR_EARLIER_THAN_TODAY2, [calEvent.start])){
				revertFunc();
			}else{
				MHSchedule.schedule.showConfirmDialog(calEvent, false, revertFunc);
				//MHSchedule.schedule.saveSchedule(calEvent,false);
			}
		},		
		events: function(start, end, callback){
			$('#calendar').fullCalendar('removeEvents');
			callback(MHSchedule.schedule.getEvents(start, end));
		},	
		eventMouseover:function(event, jsEvent, view){
			var title = event.title;
			$(this).attr('title', title);
		},
		viewDisplay: function(element) {
			MHSchedule.fullcalendar.changeViewHeight(element.name);
			MHSchedule.schedule.saveViewInfo(element);
			MHSchedule.needSaveLastView = true;
		}
	}));
};

MHSchedule.fullcalendar.changeViewHeight = function(viewName) {
	if(viewName != 'month'){
		$('#calendar').height(680);
	}else{
		var calendar = $('#calendar');
		var monthViewHeight = calendar.find(".fc-view-month").height();
		calendar.height(monthViewHeight+80);
	}		
};


/**
 * 
 * @param {} eventObject
 * 
 * FullCalendarEvent:
	{
		title: title,
		dayTitle: "",
		monthTitle: "",
		start: startDate,
		end: endDate,
		allDay: false,
		borderColor: borderColor,
		backgroundColor: backgroundColor,
		textColor: textColor,
		id: evenID,
		userID: userID,
		oldEvent:
	}  
 */
MHSchedule.fullcalendar.setFullCalendarEvent = function(eventObject) {
	var userID = eventObject.userID;
	var curUser = MHSchedule.availableUsers[userID];
	
	//if(typeof curUser == 'undefined'){
	//	return;
	//}
	if(typeof eventObject.fullname == 'undefined'){
		eventObject.fullname = curUser['fullname'];
	}
	
	//var startDateDisplay = $.fullCalendar.formatDate(eventObject.start, MHSchedule.DAYTIME_FORMAT_TITLE);
	var startDateDisplay = MHSchedule.utils.formatTimeSetting($.fullCalendar.formatDate(eventObject.start, MHSchedule.DAYTIME_FORMAT_TITLE));
	//var endDateDisplay = $.fullCalendar.formatDate(eventObject.end, MHSchedule.DAYTIME_FORMAT_TITLE);
	var endDateDisplay = MHSchedule.utils.formatTimeSetting($.fullCalendar.formatDate(eventObject.end, MHSchedule.DAYTIME_FORMAT_TITLE));
	
	//var startDateDisplay_m = $.fullCalendar.formatDate(eventObject.start, MHSchedule.DAYTIME_FORMAT_MONTH_TITLE);
	var startDateDisplay_m = MHSchedule.utils.formatTimeMSetting($.fullCalendar.formatDate(eventObject.start, MHSchedule.DAYTIME_FORMAT_MONTH_TITLE));
	
	//var endDateDisplay_m = $.fullCalendar.formatDate(eventObject.end, MHSchedule.DAYTIME_FORMAT_MONTH_TITLE);
	var endDateDisplay_m = MHSchedule.utils.formatTimeMSetting($.fullCalendar.formatDate(eventObject.end, MHSchedule.DAYTIME_FORMAT_MONTH_TITLE));
	
	//eventObject.title = curUser['first_name'] + " " + curUser['last_name'] + " " + startDateDisplay + " - " + endDateDisplay;
	eventObject.title = eventObject.fullname + " " + startDateDisplay + " - " + endDateDisplay;
	//eventObject.dayTitle = "<b>" + curUser['first_name'] + " " + curUser['last_name'] + "</b>"
	eventObject.dayTitle = "<b>" + eventObject.fullname + "</b>"
						+"<br/> <i>" + startDateDisplay + "</i>"
						+"<br/> - "
						+"<br/> <i>" + endDateDisplay + "</i>";
	if(eventObject.hasDeleted){
		var fullname = "<b class='line-through'>" + eventObject.fullname + "</b>";
	}else{
		var fullname = "<b>" + eventObject.fullname + "</b>";
	}
	eventObject.monthTitle = "<div style='text-align:left;height:29px;width:100px;line-height:14px;over-flow:hidden;padding:0;margin:0;'>"
					//	+ "<b>" + curUser['first_name'] + " " + curUser['last_name'] + "</b>"
						+ fullname
						+ "<br/> " + startDateDisplay_m + " - " + endDateDisplay_m
						+"</div>";
	
	var borderColor = MHSchedule.userColorsAssigned[userID];
//	eventObject.color = color;
	eventObject.borderColor = borderColor;
	eventObject.backgroundColor = borderColor;
	eventObject.textColor = 'black';
	eventObject.oldEvent = {
		userID: userID,
		start: new Date(eventObject.start),
		end: new Date(eventObject.end)
	};
};

MHSchedule.fullcalendar.setUndoOrRedoStatus = function(jsonData) {
	if (jsonData) {
		MHSchedule.undoSize = jsonData.undoSize;
		MHSchedule.redoSize = jsonData.redoSize;	
	}
	if (!MHSchedule.undoSize||"0"==MHSchedule.undoSize) {
		$(".fc-button-undo").addClass("fc-state-disabled");
	} else {
		$(".fc-button-undo").removeClass("fc-state-disabled");
	}
	if (!MHSchedule.redoSize||"0"==MHSchedule.redoSize) {
		$(".fc-button-redo").addClass("fc-state-disabled");
	} else {
		$(".fc-button-redo").removeClass("fc-state-disabled");
	}
};

/******************************************************** schedule *******************************************************/
MHSchedule.schedule = {};
MHSchedule.schedule.getEvents = function(start, end) {
    var fullCalendarEvents = [];
	// get events
	$.ajax({
		"url" : 'AJAX/getEvents/',
		"type" : "POST",
		"dataType" : "json",
		async: false,		
		"data" : {
            fromDate: $.fullCalendar.formatDate(start, MHSchedule.DAYTIME_FORMAT),
            toDate: $.fullCalendar.formatDate(end, MHSchedule.DAYTIME_FORMAT)
		},
		async: false,
		"success" : function(jsonData){
			var datas =  JSON.parse(jsonData.datas);
			MHSchedule.fullcalendar.setUndoOrRedoStatus(jsonData);
			$.each(datas,function(i,data){
				var eventID = data.pk;
				var userID = data.fields.oncallPerson;
				var startDate = $.fullCalendar.parseDate(data.fields.startDate, true);
				var endDate = $.fullCalendar.parseDate(data.fields.endDate, true);
				var fullCalendarEvent = {
					start: startDate,
					end: endDate,
					allDay: false,
					id: eventID,
					userID: userID,
					checkString:data.fields.checkString,
					fullname:data.fields.fullname,
					hasDeleted:data.fields.hasDeleted,
					editable:data.fields.hasDeleted?false:true
				};
				MHSchedule.fullcalendar.setFullCalendarEvent(fullCalendarEvent);	
				fullCalendarEvents.push(fullCalendarEvent);
			});
		}, // end success
		error: function(httpRequest, textStatus, errorThrown) {
			alert(MESSAGE.SCHEDULE_ERROR_GET_EVENTS);
		}
	});
	return fullCalendarEvents;
};

// undo function
MHSchedule.schedule.undo = function(obj) {
	if (MHSchedule.undoSize) {
		$.ajax({
			url: 'AJAX/undo/',
			type: 'POST',
			async: false,		
			success: function(jsonData, textStatus, httpRequest) {
				// Test for success
				if (textStatus == 'success') {
					MHSchedule.schedule.undoOrRedoCallback(jsonData);
				}
			}, // end success
			error: function(httpRequest, textStatus, errorThrown) {
				alert(MESSAGE.SCHEDULE_ERROR_UNDO);
			}
		});	
	}
};

// redo function
MHSchedule.schedule.redo = function(obj) {
	if (MHSchedule.redoSize) {
		$.ajax({
			url: 'AJAX/redo/',
			type: 'POST',
			async: false,		
			success: function(jsonData, textStatus, httpRequest) {
				// Test for success
				if (textStatus == 'success') {
					MHSchedule.schedule.undoOrRedoCallback(jsonData);
				}
			}, // end success
			error: function(httpRequest, textStatus, errorThrown) {
				alert(MESSAGE.SCHEDULE_ERROR_REDO);
			}
		});		
	}
};

MHSchedule.schedule.undoOrRedoCallback = function(jsonData) {
	$.each(jsonData.operateList,function(i,obj){
		var view = JSON.parse(obj.view);
		var viewName = view.name;
		var viewStart = view.start;
		var viewStartDate = $.fullCalendar.parseDate(viewStart);
		var viewEnd = view.end;
		var curView = $('#calendar').fullCalendar('getView');		
		var curViewName = curView.name;
		var curViewStart = $.fullCalendar.formatDate(curView.start, MHSchedule.DAYTIME_FORMAT);
		var curViewEnd = $.fullCalendar.formatDate(curView.end, MHSchedule.DAYTIME_FORMAT);
		
		if (viewName!=curViewName) {
			$('#calendar').fullCalendar('changeView', viewName);	
		}
		
		if (viewStart!=curViewStart) {
			$('#calendar').fullCalendar('gotoDate', viewStartDate.getFullYear(), viewStartDate.getMonth(), viewStartDate.getDate());
		}
		
		var type = obj.type;
		var data = JSON.parse(obj.data)[0];
		var fullCalendarEvent = {
			start: $.fullCalendar.parseDate(data.fields.startDate, true),
			end: $.fullCalendar.parseDate(data.fields.endDate, true),  
			allDay: false,
			id: data.pk,
			userID: data.fields.oncallPerson,
			checkString:data.fields.checkString
		};						
		MHSchedule.fullcalendar.setFullCalendarEvent(fullCalendarEvent);						
		if ("0" == type) {
			$('#calendar').fullCalendar('removeEvents', data.pk);
		} else if ("1" == type) {
//			fullCalendarEvent._id=fullCalendarEvent.id;
//			fullCalendarEvent._start=fullCalendarEvent.start;
//			fullCalendarEvent._end=fullCalendarEvent.end;
//			$('#calendar').fullCalendar('updateEvent', fullCalendarEvent);	
			$('#calendar').fullCalendar('removeEvents', data.pk);
			$('#calendar').fullCalendar('renderEvent', fullCalendarEvent, true);						
		} else if ("2" == type) {	
			$('#calendar').fullCalendar('renderEvent', fullCalendarEvent, true);
		}
		MHSchedule.fullcalendar.changeViewHeight(viewName);
	});
	MHSchedule.fullcalendar.setUndoOrRedoStatus(jsonData);	
};

MHSchedule.schedule.displayEventEditor = function(calEvent, isFirst, beforeCloseFunc) {
	if (calEvent != null) {
		var startDate = calEvent.start;
		var endDate = calEvent.end;
		var userID = calEvent.userID;
		var eventID = calEvent.id;
		
		var editEventDiv = $('div#scheduleOverlay_editEvent');
		var titleActionText = MESSAGE.SCHEDULE_MODIFY_DIALOG_NEW_TITLE;
		var saveText = MESSAGE.SCHEDULE_MODIFY_DIALOG_BTN_CREATE;
		if (calEvent.userID&&!isFirst) {
			titleActionText = MESSAGE.SCHEDULE_MODIFY_DIALOG_EDIT_TITLE;
			saveText = MESSAGE.SCHEDULE_MODIFY_DIALOG_BTN_UPDATE;
			$('#scheduleOverlay_editEvent_delete', editEventDiv).closest(".button").show();
		} else {
			$('#scheduleOverlay_editEvent_delete', editEventDiv).closest(".button").hide();
		}
		
		/*
		editEventDiv.overlay({
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
				fixed: false, // add by xlin to fix in IE
				// disable this for modal dialog-type of overlays
				closeOnClick: true,
				api: true, // for some reason, if api is omitted (or false), the
						  // first overlay display call is ignored.
				onBeforeClose: function(){
					if (beforeCloseFunc) {
						beforeCloseFunc();
					}
				}
			// load it immediately after the construction
			}).load();
			*/
		$(editEventDiv).dialog({
			modal:true,
			resizable:false,
			draggable:false,
			width:550,
			title:titleActionText,
			close:function(){
				if (beforeCloseFunc) {
					beforeCloseFunc();
				}
			}
		});
		
		//add by xlin for todo 1045
		if(Constant.TIME_SETTING==1){
			$('.time_setting').addClass('hidden');
		}
		var submitBtn = $('a#scheduleOverlay_editEvent_submit',editEventDiv);
		submitBtn.html(saveText);
		submitBtn.closest("div.button").removeAttr("clicked").unbind("click")
			.click(function(){
				var btn = $(this);
				if (!btn.attr("clicked")) {
					btn.attr("clicked",true);
					var form = btn.closest("form");
					if (MHSchedule.schedule.validateEventSubmission(form, calEvent)) {
						btn.removeAttr("clicked");
						return;
					}
					
					//form.closest('div#scheduleOverlay_editEvent').overlay().close();
					form.closest('div#scheduleOverlay_editEvent').dialog('close');
					MHSchedule.schedule.showConfirmDialog(calEvent, isFirst);
				}
			});
		$('a#scheduleOverlay_editEvent_close',editEventDiv).closest("div.button")
			.unbind("click")
			.click(function(){
				//$(this).closest('div#scheduleOverlay_editEvent').overlay().close();
				$(this).closest('div#scheduleOverlay_editEvent').dialog('close');
			});			
			
		if (calEvent.userID&&!isFirst) {
			$('a#scheduleOverlay_editEvent_delete',editEventDiv).closest("div.button")
				.unbind("click")
				.click(function(){
					// hide the editEvent schedule overlay.
					//$(this).closest('div#scheduleOverlay_editEvent').overlay().close();
					$(this).closest('div#scheduleOverlay_editEvent').dialog('close');
					// Now, display the new overlay.
					setTimeout(function(){
						MHSchedule.schedule.displayEventDeleteConfirmation_ShowDiv(calEvent);
					}, 250);
				});					
		}
			
		var formObj = $('form#editEvent',editEventDiv);
		
		var startJson = MHSchedule.utils.getDateJSONFromDate(calEvent.start);
		var endJson = MHSchedule.utils.getDateJSONFromDate(calEvent.end);
		
		formObj.find('input[name=start_month]').val(startJson.month);
		formObj.find('input[name=start_day]').val(startJson.day);
		formObj.find('input[name=start_year]').val(startJson.year);
		//formObj.find('input[name=start_hour]').val(startJson.hour);
		formObj.find('input[name=start_hour]').val(MHSchedule.utils.formatHours(startJson.hour,startJson.ampmVal));
		formObj.find('input[name=start_minute]').val(startJson.minute);
		formObj.find('select[name=start_ampm]').val(startJson.ampmVal);
		formObj.find('input[name=end_month]').val(endJson.month);
		formObj.find('input[name=end_day]').val(endJson.day);
		formObj.find('input[name=end_year]').val(endJson.year);
		//formObj.find('input[name=end_hour]').val(endJson.hour);
		formObj.find('input[name=end_hour]').val(MHSchedule.utils.formatHours(endJson.hour,endJson.ampmVal));
		formObj.find('input[name=end_minute]').val(endJson.minute);
		formObj.find('select[name=end_ampm]').val(endJson.ampmVal);
		
		var html = '';
		for(var i in MHSchedule.availableUsers){
			if(userID == MHSchedule.availableUsers[i].id){
				html += '<option selected="selected" value="' + MHSchedule.availableUsers[i].id + '">' + MHSchedule.availableUsers[i].fullname + '</option>';
			}else{
				html += '<option value="' + MHSchedule.availableUsers[i].id + '">' + MHSchedule.availableUsers[i].fullname + '</option>';
			}
		}
		formObj.find('select[name=scheduleOverlay_userList]').html(html);
	}
};

//add by xlin 20120223 conflict confirm dialog
MHSchedule.schedule.showConfirmDialog = function(calEvent, isFirst, cancelFunc){
	var conflictName = {};
	var conflictTime = '';
	var isConflict = false;
	var events = $('#calendar').fullCalendar('clientEvents');
	var len = events.length;
	var html = '';
	for(var i=0; i<len; i++){
		if(calEvent.checkString!=events[i].checkString){
			if(calEvent.start>=events[i].end || calEvent.end<=events[i].start){
				isConflict = false;
			}else{
				isConflict = true;
				break;
			}
		}
	}
	
	for(var i=0; i<len; i++){
		if(calEvent.checkString!=events[i].checkString){
			if(calEvent.start>=events[i].end || calEvent.end<=events[i].start){
				continue;
			}else{
//				var id = events[i]['userID'];
//				var name = MHSchedule.availableUsers[id]['first_name']+' '+MHSchedule.availableUsers[id]['last_name'];
//				conflictName[name]=i;
				var name = events[i]['fullname'];
				conflictName[name]=i;
			}
		}
	}
	if(isConflict){
		var html = MHSchedule.schedule.displayProviders(conflictName, calEvent);
		var isCancel = true;
		$('#confirmDialog h3').html(html);
		$('#confirmDialog').dialog({
			buttons:{
				'Cancel':function(){
					if (cancelFunc) {
						isCancel = false;
						cancelFunc();
					}
					$('#confirmDialog h3').html('');
					$(this).dialog('close');
					return false;
				},
				'Confirm':function(){
					isCancel = false;
					$(this).dialog('close');
					MHSchedule.schedule.saveSchedule(calEvent,isFirst);
				}
			},
			draggable:false,
			width:550,
			modal:true,
			resizable:false,
			title:MESSAGE.SCHEDULE_MODIFY_CONFIRM_DIALOG_TITLE,
			open:function(){
				var btns = $(this).parent().find('.ui-dialog-buttonset button');
				btns.eq(1).addClass('gradually');
				btns.eq(0).trigger("blur");
			},
			close:function(){
				if (cancelFunc && isCancel) {
					cancelFunc();
				}
				$('#confirmDialog h3').html('');
				return false;
			}
		});
	}else{
		MHSchedule.schedule.saveSchedule(calEvent,isFirst);
	}
};

//add by xlin 20120207 return html for a provider or some providers
MHSchedule.schedule.displayProviders = function(conflictName, calEvent){
	var html = '';
	var name = new Array();
	for(var key in conflictName){
		name.push(key);
	}
	var _len = name.length;
	if(_len == 1){
		html += 'A provider ' + name[0];
	}else if(_len == 2){
		html += 'Providers '+ name[0] + ' and '+ name[1];
	}else{
		html += 'Providers ';
		for(var i=0; i<_len-1; i++){
			if(i != _len - 2){
				html += name[i] + ', ';
			}else{
				html += name[i];
			}
			
		}
		html += ' and '+ name[_len-1];
	}
	html+=' already scheduled for on-call during this time slot from ';
	html+= $.fullCalendar.formatDate(calEvent.start, MHSchedule.DAYTIME_FORMAT_TITLE);
	html+=' to '+ $.fullCalendar.formatDate(calEvent.end, MHSchedule.DAYTIME_FORMAT_TITLE) + '. </p>';
	html+='<p>'+MESSAGE.SCHEDULE_MODIFY_CONFIRM_DIALOG_CHECK_INFO+'</p>';
	return html;
};

MHSchedule.schedule.displayEventDeleteConfirmation_ShowDiv = function(calEvent) {
	if(typeof calEvent.fullname == 'undefined'){
		calEvent.fullname = MHSchedule.availableUsers[calEvent.userID]['fullname'];
	}
	var startJson = MHSchedule.utils.getDateJSONFromDate(calEvent.start);
	var endJson = MHSchedule.utils.getDateJSONFromDate(calEvent.end);
	
	if(!MHSchedule.schedule.checkCurrentDate(MESSAGE.SCHEDULE_ERROR_EARLIER_THAN_TODAY4, [calEvent.start])){
		return;
	}
	
	var deleteConfirmDiv = $('div#scheduleOverlay_deleteEvent');
	
	var startTD = $('span#deleteConfirmOverlay_start', deleteConfirmDiv);
	startTD.empty();
	var t1 = MHSchedule.utils.deleteFormatTime(startJson.hour,startJson.minute,startJson.ampm);
	startTD.html(startJson.month+'/'+startJson.day+'/'+startJson.year+
			' at '+t1);
	
	var endTD = $('span#deleteConfirmOverlay_end', deleteConfirmDiv);
	endTD.empty();
	var t2 = MHSchedule.utils.deleteFormatTime(endJson.hour,endJson.minute,endJson.ampm);
	endTD.html(endJson.month+'/'+endJson.day+'/'+endJson.year+
			' at '+t2);
	
	userTD = $('span#deleteConfirmOverlay_onCall', deleteConfirmDiv);
	userTD.empty();
	//userTD.html(MHSchedule.availableUsers[calEvent.userID]['first_name']+' '+MHSchedule.availableUsers[calEvent.userID]['last_name']);
	userTD.html(calEvent.fullname);
	/*
	var overlay = deleteConfirmDiv.overlay({

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
			fixed: false, // add by xlin to fix in IE
			// disable this for modal dialog-type of overlays
			closeOnClick: true,
			api: true // for some reason, if api is omitted (or false), the
					  // first overlay display call is ignored.

		// load it immediately after the construction
		}).load();*/
	
	$(deleteConfirmDiv).dialog({
		modal:true,
		resizable:false,
		draggable:false,
		width:550,
		title:MESSAGE.SCHEDULE_DELETE_CONFIRM_DIALOG_TITLE,
		open:function(){
			var btns = $(this).parent().find('.close').trigger("blur");
		}
	});
	
	$('a#scheduleOverlay_editEvent_cancelDelete',deleteConfirmDiv).parent()
		.unbind("click")
		.click(function(){
			// hide the editEvent schedule overlay.
			//$(this).closest('div#scheduleOverlay_deleteEvent').overlay().close();
			$(this).closest('div#scheduleOverlay_deleteEvent').dialog('close');				
		});		
		
	$('a#scheduleOverlay_editEvent_confirmDelete',deleteConfirmDiv).parent()
		.removeAttr("clicked")
		.unbind("click")
		.click(function(){
			var btn = $(this);
			if (!btn.attr("clicked")) {
				btn.attr("clicked",true);
				MHSchedule.schedule.saveSchedule(calEvent, false, true);
				// hide the editEvent schedule overlay.
				//$(this).closest('div#scheduleOverlay_deleteEvent').overlay().close();
				$(this).closest('div#scheduleOverlay_deleteEvent').dialog('close');			
			}			
		});			
};

MHSchedule.schedule.saveSchedule = function(calEvent, isFirst, isDelete) {
	if (isFirst) {
		MHSchedule.schedule.saveNewEvents(calEvent);
	} else {
		MHSchedule.schedule.saveUpdatedEvents(calEvent, isDelete);
	}
};

//add by xlin in 20120528 for bug 598 that before save event check user is in call group TODO
MHSchedule.schedule.checkeUserInCallGroup = function(calEvent){
	var callgroup_id=location.pathname.split('/')[2];
	var userId=calEvent.userID;
	var isExist=false;
	$.ajax({
		url:'AJAX/checkeUserInCallGroup/',
		type:'POST',
		data:{
			'userId':userId,
			'callgroup_id':callgroup_id
		},
		async: false,
		success:function(data,txtStatus){ //TODO
			var d=JSON.parse(data);
			if(d=='ok'){
				isExist=true;
			}
		},
		error:function(data,txtStatus){
			alert(MESSAGE.SCHEDULE_ERROR_CHECKE_USER);
			location.reload(true);
		}
	});
	return isExist;
};

MHSchedule.schedule.saveNewEvents = function(calEvent) {
	// Build JSON for the new events.
	var b = MHSchedule.schedule.checkeUserInCallGroup(calEvent);
	if(b){
		var checkString = MHSchedule.utils.randomString(); 
		var newEventsJSON = [{
				pk: null,
				model: "Scheduler.evententry",
				fields: {
					oncallPerson: calEvent.userID,
					eventType: $('input[name="type"]').val(),
					startDate: $.fullCalendar.formatDate(calEvent.start, MHSchedule.DAYTIME_FORMAT),
					endDate: $.fullCalendar.formatDate(calEvent.end, MHSchedule.DAYTIME_FORMAT),			
					checkString: checkString
				}
			}];		
	
		// Convert the array and all nested objects into JSON text.
		newEventsJSON = JSON.stringify(newEventsJSON);
		
		var curView = $('#calendar').fullCalendar('getView');
		$.ajax({
			url: 'AJAX/newEvents/',
			type: 'POST',
			async: false,
			data: {
				data:newEventsJSON,
				view:JSON.stringify({
					name: curView.name,
					start: $.fullCalendar.formatDate(curView.start, MHSchedule.DAYTIME_FORMAT),
					end: $.fullCalendar.formatDate(curView.end, MHSchedule.DAYTIME_FORMAT)
				})		
			}, // end data
			
			success: function(jsonData, textStatus, httpRequest) {
				// Test for success
				if (textStatus == 'success') {
					calEvent.checkString = checkString;
					calEvent.id = jsonData["data"][checkString];
					MHSchedule.fullcalendar.setFullCalendarEvent(calEvent);				
					$('#calendar').fullCalendar('renderEvent', calEvent, true);
					MHSchedule.fullcalendar.setUndoOrRedoStatus(jsonData);
					MHSchedule.fullcalendar.changeViewHeight(curView.name);
				}
			}, // end success
			error: function(httpRequest, textStatus, errorThrown) {
				alert(MESSAGE.SCHEDULE_ERROR_ADD);
				window.location.reload();
			}
		});
		MHSchedule.schedule.rulecheckEvents();
	}else{
		alert(MESSAGE.SCHEDULE_USER_NOT_IN_GROUP);
		location.reload(true);
	}
};

MHSchedule.schedule.saveUpdatedEvents = function (calEvent, isDelete) {
	var oldEvent = calEvent.oldEvent;
	if (isDelete||oldEvent.userID!=calEvent.userID
		||Date.parse(oldEvent.start)!=Date.parse(calEvent.start)||Date.parse(oldEvent.end)!=Date.parse(calEvent.end)) {
		// Find and store all changed events
		var start = $.fullCalendar.formatDate(calEvent.start, MHSchedule.DAYTIME_FORMAT);
		var end = $.fullCalendar.formatDate(calEvent.end, MHSchedule.DAYTIME_FORMAT);
		var changedEventsJSON = [{
					pk: calEvent.id,
					model: "Scheduler.evententry",
					fields: {
						oncallPerson: calEvent.userID,
						eventType: $('input[name="type"]').val(),
						startDate: start,
						endDate: end,
						eventStatus: (isDelete) ? 0 : 1,
						checkString: calEvent.checkString
					}
				}]; 
		
		// Convert the array and all nested objects into JSON text.
		changedEventsJSON = JSON.stringify(changedEventsJSON);
		var curView = $('#calendar').fullCalendar('getView');
		$.ajax({
			url: 'AJAX/updateEvents/',
			type: 'POST',
			async: false,		
			data: {
				data:changedEventsJSON,
				view:JSON.stringify({
					name: curView.name,
					start: $.fullCalendar.formatDate(curView.start, MHSchedule.DAYTIME_FORMAT),
					end: $.fullCalendar.formatDate(curView.end, MHSchedule.DAYTIME_FORMAT)
				})
			}, // end data
			
			success: function(jsonData, textStatus, httpRequest) {
				// Test for success
				if (textStatus == 'success') {
					if (isDelete) {
						$('#calendar').fullCalendar('removeEvents', calEvent.id);	
					} else {
						MHSchedule.fullcalendar.setFullCalendarEvent(calEvent);		
						$('#calendar').fullCalendar('updateEvent', calEvent);					
					}
					MHSchedule.fullcalendar.setUndoOrRedoStatus(jsonData);
					MHSchedule.fullcalendar.changeViewHeight(curView.name);
				}
			}, // end success
			error: function(httpRequest, textStatus, errorThrown) {
				alert(MESSAGE.SCHEDULE_ERROR_UPDATE);
				window.location.reload();
			}
		});	
		MHSchedule.schedule.rulecheckEvents();
	}
};

MHSchedule.schedule.rulecheckEvents = function() {
	/* checks events for the given date range, if there are any holes in coverage
	 * This function should always be called after updates to check for holes in coverage
	 */
	$.ajax({
		url: 'AJAX/rulesCheck/',
		type: 'POST',
		async: false,		
		data: {
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
		}, // end success
		error: function(httpRequest, textStatus, errorThrown) {
			alert(MESSAGE.SCHEDULE_ERROR_CHECK_RULE);
		}
	});
};

MHSchedule.displayErrorInPopup = function(html) {
	//MHSchedule.errWin = window.open('', '', 'width=800,height=600,scrollbars=yes,toolbar=yes');
	//MHSchedule.errWin.document.write(html);
};

MHSchedule.schedule.checkCurrentDate = function(errorMsg, dates) {
	/*var currentDate = null;
	$.ajax({
		url: 'AJAX/getCurrentDate/',
		type: 'GET',
		async: false,	
		success: function(data, textStatus, httpRequest) {
			if (textStatus == 'success') {
				currentDate = $.fullCalendar.parseDate(data.currentDate, true);
			}
		}, // end success
		error: function(httpRequest, textStatus, errorThrown) {
			currentDate = null;
		}
	});	
	
	var retVal = false;
	if (currentDate) {
		if (dates) {
			retVal = true;
			$.each(dates, function(i, date){
				if (date < currentDate){
					alert(errorMsg);
					retVal = false;
					return false;
				}
			});
		}	
	} else {
		alert(MESSAGE.SCHEDULE_ERROR_GET_SERVER_TIME);
		retVal = false;
	}
	return retVal;*/
	return true;
};

// form validate and set start/end/userID to calEvent if validate successfully.
MHSchedule.schedule.validateEventSubmission = function(form, calEvent) {
	
	var numericRegex = new RegExp('^[0-9]+$');
	var startYear = form.find('input[name=start_year]').val();
	var startMonth = form.find('input[name=start_month]').val() - 1;
	var startDay = form.find('input[name=start_day]').val();
	var startHour = form.find('input[name=start_hour]').val();
	var startMinute = form.find('input[name=start_minute]').val();
	var startAMPM = form.find('select[name=start_ampm]').val();
	
	var endYear = form.find('input[name=end_year]').val();
	var endMonth = form.find('input[name=end_month]').val() - 1;
	var endDay = form.find('input[name=end_day]').val();
	var endHour = form.find('input[name=end_hour]').val();
	var endMinute = form.find('input[name=end_minute]').val();
	var endAMPM = form.find('select[name=end_ampm]').val();
	
	var eventType = form.find('input[name=type]').val();
	var userID = $('select[name="scheduleOverlay_userList"]',form).val();
	
	var fname = '';
	$('select[name="scheduleOverlay_userList"] option').each(function(){
		if($(this).val()==userID){
			fname = $(this).text();
		}
	});

	if (!(eventType == 0 || eventType == 1)) {
		alert(MESSAGE.SCHEDULE_ERROR_VALIDATE_EVENTTYPE);
		return 1;
	}
	
	if (startYear.length != 4 || !(numericRegex.test(startYear)) ||
					!(startYear >= 2009 && startYear <= 2099)) {
		alert(MESSAGE.SCHEDULE_ERROR_VALIDATE_START_YEAR);
		return 1;
	}
	if (startMonth.length > 2 || !(numericRegex.test(startMonth)) ||
					!(startMonth >= 0 && startMonth <= 11)) {
		alert(MESSAGE.SCHEDULE_ERROR_VALIDATE_START_MONTH);
		return 1;
	}
	if (startDay.length > 2 || !(numericRegex.test(startDay))
					|| !(startDay >= 1 && startDay <= 31)) {
		alert(MESSAGE.SCHEDULE_ERROR_VALIDATE_START_DATE);
		return 1;
	}
	// checkDayValidity checks the day validity given the month and year.
	if (MHSchedule.utils.checkDayValidity(startYear, startMonth, startDay)) {
		alert(MESSAGE.SCHEDULE_ERROR_VALIDATE_START_MONTH_DATE);
		return 1;
	}
	
	if(Constant.TIME_SETTING==1){ //12
		if (startHour.length > 2 || !(numericRegex.test(startHour))
			|| !(startHour >= 0 && startHour <= 23)) {
			alert(MESSAGE.SCHEDULE_ERROR_VALIDATE_HOUR2);
			return 1;
		}
	}else{ //24
		if (startHour.length > 2 || !(numericRegex.test(startHour))
			|| !(startHour >= 1 && startHour <= 12)) {
			alert(MESSAGE.SCHEDULE_ERROR_VALIDATE_START_HOUR);
			return 1;
		}
	}
	
	if (startMinute.length > 2 || !(numericRegex.test(startMinute))
					|| !(startMinute >= 0 && startMinute <= 59)) {
		alert(MESSAGE.SCHEDULE_ERROR_VALIDATE_START_MINUTE);
		return 1;
	}
	
	
	if (endYear.length != 4 || !(numericRegex.test(endYear)) ||
					!(endYear >= 2009 && endYear <= 2099)) {
		alert(MESSAGE.SCHEDULE_ERROR_VALIDATE_END_YEAR);
		return 1;
	}
	if (endMonth.length > 2 || !(numericRegex.test(endMonth)) ||
					!(endMonth >= 0 && endMonth <= 11)) {
		alert(MESSAGE.SCHEDULE_ERROR_VALIDATE_END_MONTH);
		return 1;
	}
	if (endDay.length > 2 || !(numericRegex.test(endDay))
					|| !(endDay >= 1 && endDay <= 31)) {
		alert(MESSAGE.SCHEDULE_ERROR_VALIDATE_END_DATE);
		return 1;
	}
	// checkDayValidity checks the day validity given the month and year.
	if (MHSchedule.utils.checkDayValidity(endYear, endMonth, endDay)) {
		alert(MESSAGE.SCHEDULE_ERROR_VALIDATE_END_MONTH_DATE);
		return 1;
	}
	
	if(Constant.TIME_SETTING==1){ //12
		if (endHour.length > 2 || !(numericRegex.test(endHour)) 
				|| !(endHour >= 0 && endHour <= 23)) {
			alert(MESSAGE.SCHEDULE_ERROR_VALIDATE_HOUR2);
			return 1;
		}
	}else{
		if (endHour.length > 2 || !(numericRegex.test(endHour)) 
				|| !(endHour >= 1 && endHour <= 12)) {
			alert(MESSAGE.SCHEDULE_ERROR_VALIDATE_END_HOUR);
			return 1;
		}
	}
	
	if (endMinute.length > 2 || !(numericRegex.test(endMinute)) || !(endMinute >= 0 && endMinute <= 59)) {
		alert(MESSAGE.SCHEDULE_ERROR_VALIDATE_END_MINUTE);
		return 1;
	}
	
	if(Constant.TIME_SETTING==1){ //12
		var startDate = new Date(startYear, startMonth, startDay, startHour, startMinute);
		var endDate = new Date(endYear, endMonth, endDay, endHour, endMinute);
	}else{
		var startDate = new Date(startYear, startMonth, startDay, MHSchedule.utils.getHour(startHour, startAMPM), startMinute);
		var endDate = new Date(endYear, endMonth, endDay, MHSchedule.utils.getHour(endHour, endAMPM), endMinute);
	}
	//compare start date with today
	if(!MHSchedule.schedule.checkCurrentDate(MESSAGE.SCHEDULE_ERROR_EARLIER_THAN_TODAY1, [startDate])){
		return 1;
	}

	if (endDate <= startDate) {
		alert(MESSAGE.SCHEDULE_ERROR_VALIDATE_START_END);
		return 1;
	}
	
	for (id in MHSchedule.availableUsers) {
		if (userID == id) {
			calEvent.start = startDate;
			calEvent.end = endDate;
			calEvent.userID = userID;
			calEvent.fullname = fname;
			calEvent.hasDeleted = 0;
			return 0;
		}
	}
	
	// User ID isn't in the set of valid user IDs. reject it.
	alert(MESSAGE.SCHEDULE_ERROR_VALIDATE_INVALID_USER);
	return 1;
};

MHSchedule.schedule.getDuration = function(start, end) {
	var valid = true;
	var startDate = new Date();
	
	if (start) {
		startDate = new Date(start);
	}
	
	var endDate = new Date();
	if (end) {
		endDate = new Date(end);
	} else if (start) {
		endDate = new Date(start);
	}
	
	var startHour = $('#startHour').val();
	var startMin = $('#startMin').val();
	var endHour = $('#endHour').val();
	var endMin = $('#endMin').val();
	var startAM = $('#startMoring').val();
	var endAM = $('#endMoring').val();
	
	if(isNaN(startHour) || isNaN(startMin) || isNaN(endHour) || isNaN(endMin) || startHour=='' || endHour=='' || startMin==''|| endMin==''){
		valid = false;
		alert('Time is invalid.');
	}else{
		if(Constant.TIME_SETTING==1){ //24h start hour and end hour can be 0
			if(startHour < 0 || startHour > 23 || endHour < 0 || endHour > 23){
				valid = false;
				alert(MESSAGE.SCHEDULE_ERROR_VALIDATE_HOUR2);
			}
		}else{
			if(startHour < 1 || startHour > 12 || endHour < 1 || endHour > 12){
				valid = false;
				alert(MESSAGE.SCHEDULE_ERROR_VALIDATE_HOUR);
			}
		}
		
		if(startMin < 0 || startMin > 59 || endMin < 0 || endMin > 59){
			valid = false;
			alert(MESSAGE.SCHEDULE_ERROR_VALIDATE_MINUTE);
		}

		startHour = MHSchedule.utils.getHour(startHour, startAM);
		startDate.setHours(startHour);
		startDate.setMinutes(startMin);
		
		endHour = MHSchedule.utils.getHour(endHour, endAM);
		endDate.setHours(endHour);
		endDate.setMinutes(endMin);
		
		if(endDate <= startDate){
			endDate.setDate(startDate.getDate()+1);
		}
	}
	return {
		valid: valid,
		start: startDate,
		end: endDate
	};
};

MHSchedule.schedule.saveViewInfo = function(view) {
	if (view && MHSchedule.needSaveLastView && (view.name != MHSchedule.lastView.name || view.start > MHSchedule.lastView.start || view.start < MHSchedule.lastView.start)) {
		$.ajax({
			url: 'AJAX/saveViewInfo/',
			type: 'POST',
			async: false,		
			data: {
				view:JSON.stringify({
					name: view.name,
					start: $.fullCalendar.formatDate(view.start, MHSchedule.DAYTIME_FORMAT),
					end: $.fullCalendar.formatDate(view.end, MHSchedule.DAYTIME_FORMAT)
				})
			}, // end data
			success: function(data, textStatus, httpRequest) {
				if (textStatus == 'success') {
					MHSchedule.lastView = {
						name: view.name,
						start: new Date(view.start),
						end: new Date(view.end)
					};
				}
			}, // end success
			error: function(httpRequest, textStatus, errorThrown) {
			}
		});	
	}
};

MHSchedule.schedule.getViewInfo = function() {
	var currentDate = new Date();
	var view = {
//		defaultView: "agendaWeek",
		year: currentDate.getFullYear(),
		month: currentDate.getMonth(),
		date: currentDate.getDate()
	};
	$.ajax({
		url: 'AJAX/getViewInfo/',
		type: 'GET',
		async: false,		
		success: function(data, textStatus, httpRequest) {
			if (textStatus == 'success') {
				var savedView = JSON.parse(data.view);
				if (savedView) {
					var savedStartDate = $.fullCalendar.parseDate(savedView.start, true);
					if (savedStartDate>currentDate) {
						view = {
							defaultView: savedView.name,
							year: savedStartDate.getFullYear(),
							month: savedStartDate.getMonth(),
							date: savedStartDate.getDate()					
						};					
					} else {
						view.defaultView = savedView.name;
					}
				}
			}
		}, // end success
		error: function(httpRequest, textStatus, errorThrown) {
		}
	});	
	return view;
};

/******************************************************** pdf download *************************************************/
MHSchedule.pdf = {};
MHSchedule.pdf.clickPrevYear = function(currentYear){
	var y = parseInt($('#calendar2 .year').text());
	if(y > currentYear - 5 ){
		y = y -1;
	}
	$('#calendar2 .year').text(y);
};

MHSchedule.pdf.clickNextYear = function(currentYear){
	var y = parseInt($('#calendar2 .year').text());
	if(y < currentYear + 10){
		y = y +1;
	}
	$('#calendar2 .year').text(y);
};

MHSchedule.pdf.downloadPDF = function(){
	var year = parseInt($('#calendar2 .year').text());
	var month = 0;
	$("#calendar2 td").each(function(i){
		if($(this).hasClass("currentMonth")){
			month = i + 1;
		}
	});
	var groupId = location.href.split('/')[4];
	MHSchedule.pdf.ajaxDownloadPDF(groupId,year,month);
};

MHSchedule.pdf.ajaxDownloadPDF = function(id,year,month){
	if(isIPad()){
		window.open("/CallGroup/" + id + "/Schedule/Print/?year=" + year + "&month=" +  month);
	}else{
		location.href = "/CallGroup/" + id + "/Schedule/Print/?year=" + year + "&month=" +  month;
	}
};

// download pdf function
MHSchedule.pdf.downloadPDFDialog = function() {
	//$('#downloadPDFDialog').overlay().load();
	$('#downloadPDFDialog').dialog({
		modal:true,
		resizable:false,
		draggable:false,
		width:550,
		title:MESSAGE.SCHEDULE_DOWNLOAD_DIALOG_TITLE
	});
};

/******************************************************** utils ********************************************************/
MHSchedule.utils = {};
MHSchedule.utils.getDateJSONFromDate = function(date) {
	var year = date.getFullYear();
	var month = date.getMonth()+1;
	month = month.toString().length == 1 ? '0'+month : month;	
	var day = date.getDate();
	day = day.toString().length == 1 ? '0'+day : day;
	
	var hour = date.getHours();
	var ampm = hour <= 11 ? 'AM' : 'PM';
	var ampmVal = hour <= 11 ? '0' : '1';
	
	if(Constant.TIME_SETTING==0){
		hour = hour%12;
		if (0==hour) {
			hour = 12;
		}
	}
	
	hour = hour.toString().length == 1 ? '0'+hour : hour;	
	
	var minute = date.getMinutes();
	minute = minute.toString().length == 1 ? '0'+minute : minute;
	
	return {
		year: year,
		month: month,
		day: day,
		hour: hour,
		minute: minute,
		ampm: ampm,
		ampmVal: ampmVal
	};
};

MHSchedule.utils.getHour = function(hour, ampm) {
	var h = parseInt(hour, 10);
	if(typeof ampm == 'undefined'){
		return h;
	}
	if(ampm == '1'){
		if (h == 12) {
			return 12;
		} else {
			return h + 12;
		}
	}else {
		if(h==12){
			h=0
		}
		return h;
	}
};

MHSchedule.utils.randomString = function(length, chars) {
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
};

MHSchedule.utils.checkDayValidity = function(year, month, day) {
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
};

//add by xlin for todo1045 121018
//Constant.TIME_SETTING
MHSchedule.utils.formatTimeSetting = function(time){
	var t = time;
	if(Constant.TIME_SETTING){ //1
		if(t.indexOf('am')>-1){ //am
			var t1 = t.substring(6,8);
			if(t1=='12'){
				t = t.substring(0,6) + '00'+t.substring(8,11);
			}else{
				t = t.substring(0,11);
			}
			t = t.substring(0,11);
		}else{ //pm
			var t1 = t.substring(0,6);
			var t4 = parseInt(t.substring(6,8),10);
			if(t4==12){
				t4=0;
			}
			var t2 = t4+12;
			var t3 = t.substring(8,12);
			t = t1+t2+t3;
		}
	}
	return t;
};

//08:00
//20:00
MHSchedule.utils.formatTimeMSetting = function(time){
	var t = time;
	if(!Constant.TIME_SETTING){ //1
		var t1 = parseInt(t.split(':')[0],10);
		var t2 = t.substring(2,5);
		if(t1<12){
			if(t1==0){
				t1=12;
			}
			t = (''+t1).length>1?t1:('0'+t1);
			t = t + t2 + ' am';
		}else{
			if(t1==12){
				t = '12';
			}else{
				t = (''+(t1-12)).length>1?(t1-12):('0'+(t1-12));
			}
			t = t + t2 + ' pm';
		}
	}
	return t;
};

//according hour and am to translate
MHSchedule.utils.formatHours = function(hour,am){
	var h = parseInt(hour,10);
	if(am == 1&& h==24){
		h = '00';
	}
	if(h.length<2 || h<10){
		h='0'+h;
	}
	return h;
};

//add by xlin 121105
MHSchedule.utils.deleteFormatTime =function(h,m,am){
	//endJson.hour+':'+endJson.minute+' '+endJson.ampm
	var t = '';
	var hour = parseInt(h,10);
	if(Constant.TIME_SETTING){ //1
		if(hour<12 && am == 1){
			t = hour+12;
		}else{
			t= hour
		}
		t = (''+t).length>1?t:('0'+t);
		t = t +':'+m;
	}else{
		t = h+':'+m+':'+am;
	}
	return t;
};