$(function(){
	MHSchedule.WeekModule.switchModes(); // Default to weekly for now.
	MHSchedule.init();
	
	//$('div#calendar_clickable').click(schedule_newEventByClick);
	
	var datePickerConfig = {};
	datePickerConfig.startDay = MHSchedule.startDay;
	
	datePickerConfig.today = new Date();
	datePickerConfig.today.setHours(0,0,0,0);
	// datePickerConfig.today.setDate(datePickerConfig.today.getDate()-8); // Used for debugging/testing
	datePickerConfig.minDate = new Date(datePickerConfig.today.getTime());
	datePickerConfig.minDate.setHours(0,0,0,0);
	if (datePickerConfig.minDate.getDay() < datePickerConfig.startDay && datePickerConfig.startDay != 0) {
		datePickerConfig.minDate.setDate(datePickerConfig.minDate.getDate() - 7);
	}
	datePickerConfig.minDate.setDate(datePickerConfig.minDate.getDate() - datePickerConfig.minDate.getDay() + datePickerConfig.startDay);
	datePickerConfig.maxDate = new Date(datePickerConfig.minDate.getTime());
	datePickerConfig.maxDate.setDate(datePickerConfig.maxDate.getDate() + 6);
	
	var dPick = $('div#calendar_nav').datepicker({
			flat: true,
			date: [datePickerConfig.minDate, datePickerConfig.maxDate],
			current: datePickerConfig.today,
			format: 'Y-m-d',
			calendars: 1,
			starts: datePickerConfig.startDay,
			mode: 'range',
			custom_mode: 'weekly',
			showOtherMonths: true,
			dayNamesMin:['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'],
			//prevText: '<b>&lt;</b>',
			//nextText: '<b>&gt;</b>',
			onRender: function(date) {
				/*
				return {
					disabled: (date.valueOf() < datePickerConfig.minDate.valueOf()),
					className: date.valueOf() == datePickerConfig.today.valueOf() ? 'datepickerSpecial' : false
				}*/
			},/*
			onChange: function(formated, dates) {
				MHSchedule.currentModule.changeDates(dates);
			}*/
			onSelect: function(dateText, inst){
			
				var datePickerConfig = {};
				datePickerConfig.startDay = MHSchedule.startDay;
				
				datePickerConfig.today = new Date(dateText);
				datePickerConfig.today.setHours(0,0,0,0);
				// datePickerConfig.today.setDate(datePickerConfig.today.getDate()-8); // Used for debugging/testing
				datePickerConfig.minDate = new Date(datePickerConfig.today.getTime());
				datePickerConfig.minDate.setHours(0,0,0,0);
				if (datePickerConfig.minDate.getDay() < datePickerConfig.startDay && datePickerConfig.startDay != 0) {
					datePickerConfig.minDate.setDate(datePickerConfig.minDate.getDate() - 7);
				}
				datePickerConfig.minDate.setDate(datePickerConfig.minDate.getDate() - datePickerConfig.minDate.getDay() + datePickerConfig.startDay);
				datePickerConfig.maxDate = new Date(datePickerConfig.minDate.getTime());
				datePickerConfig.maxDate.setDate(datePickerConfig.maxDate.getDate() + 6);
				
				$('#calendar_nav .ui-state-active').parent().parent().addClass("orange");
				MHSchedule.currentModule.changeDates([datePickerConfig.minDate, datePickerConfig.maxDate]);
			}
		});
	//var temp = dPick.DatePicker();
	MHSchedule.currentModule.changeDates([datePickerConfig.minDate, datePickerConfig.maxDate]);
	//show current week
	$('#calendar_nav .ui-state-active').parent().parent().addClass("orange");
	
	//$("#dragged_new_event_config p").index($("p.ui-state-active"));
	//MHSchedule.Accordion = $('#dragged_new_event_config').accordion({active:0});
	
	//load pdf down dialog
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
	});
	//show current month and year, so stupid ie
	var ie = !-[1,];
	if(ie){
		var currentYear = (new Date).getYear();
	}else{
		var currentYear = (new Date).getYear()+1900;
	}
	$('#calendar .year').text(currentYear);
	var month = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];
	$('#calendar .content td').each(function(){
		var currentMonth = (new Date()).getMonth();
		if(month[currentMonth]==$(this).find('span').text()){
			$(this).addClass('currentMonth');
		}
	});
	
	$('#calendar .prev').click(function(){
		MHSchedule.clickPrevYear(currentYear);
	});
	
	$('#calendar .next').click(function(){
		MHSchedule.clickNextYear(currentYear);
	});
	
	$('#calendar td').click(function(){
		$('#calendar td').removeClass('currentMonth');
		$(this).addClass('currentMonth');
	});
	
	$("#dragged_new_event_config .title .help_icon").hover(function(event){
		var left = event.clientX;
		var top = event.clientY - 50;
		$('#help1_content').css({
			'left':left+'px',
			'top':top+'px'
		});
		$('#help1_content').removeClass('hidden');
		return false;
	},function(){
		$('#help1_content').addClass('hidden');
	});
	
	$("#dragged_new_event_config .duration .help_icon2").hover(function(event){
		var left = event.clientX;
		var top = event.clientY - 50;
		$('#help2_content').css({
			'left':left+'px',
			'top':top+'px'
		});
		$('#help2_content').removeClass('hidden');
		return false;
	},function(){
		$('#help2_content').addClass('hidden');
	});
	
	$('#calendar_save_warning .right').click(function(){
		$('#calendar_save_warning').hide(500);
	});
});