// Schedule library object -- this helps to keep the global namespace clear.
var MHSchedule = {};


MHSchedule.init = function() {
	$('#calendar_save_warning').hide();
	
	//MHSchedule.getCallGroupMembers();
	MHSchedule.refreshCallGroupMembers();
	
	// getting events is handled by the display module (e.g., week, month)
	//MHSchedule.getEvents(MHSchedule.baseDate, MHSchedule.endDate);
	
}

MHSchedule.displaySaveWarning = function() {
	var html = 'Unsaved changes have been made. You must <a href="javascript:MHSchedule.saveSchedule()">save</a> to apply these changes.<br />Alternatively, you may <a href="javascript:location.reload(true)">revert</a> to the previously saved version.';
	$('#calendar_save_warning').html(html);
	$('#calendar_save_warning').show(500);
}


/*
 * Call Group Members
 */

/* The availableUserIds associative array shall be keyed on the user's ID. Each
 * value shall be the user's full name.
 */
MHSchedule.availableUsers = {};

MHSchedule.getCallGroupMembers = function() {
	/* Get the call groups members. I'm assuming they come in the following
	 * format:
	 * [ {id: <id>, first_name: <first name>, last_name: <last_name>},
	 *   {...},
	 *   ...
	 * ]
	 */
	for (var i=0; i < MHSchedule.sampleUsers.length; i++) {
		MHSchedule.availableUsers[MHSchedule.sampleUsers[i]['id']] = {
					first_name: MHSchedule.sampleUsers[i]['first_name'],
					last_name: MHSchedule.sampleUsers[i]['last_name']
			};
		MHSchedule.userColorsAssigned[MHSchedule.sampleUsers[i]['id']] = MHSchedule.userColorsAvailable[MHSchedule.userColorsAssignedCounter++];
	}
}

MHSchedule.userColorsAvailable = [
	'#8accd9', '#9a81ee', '#e187be',
	'#dcd069', '#88e859', '#f2a948',
	'#d1d1d1', '#6f97f3', '#ff6b6b',
	'#c5e084', '#ba9976', '#33ca3a',
	'#eec19c', '#8d30ce', '#d40000'
	//'#', '#', '#',
];
// The following is an associative array, keyed on the user's ID, to get the
// color for that user's events.
MHSchedule.userColorsAssigned = {};
MHSchedule.userColorsAssignedCounter = 0; 


/* JavaScript array here.
 * 
 * The following is a JavaScript array reference for Brian.
 * 
 * append: array.push(value)
 * delete: array.splice(index)
 */

MHSchedule.events = {};
MHSchedule.newEvents = []; // Events not in the server yet
MHSchedule.undoLevels = 0; // keeps track of how many undo levels we have until
							// we've reverted to the original state.
//var undoLevels = 0; // keeps track of how many undo levels we have until we've
					// reverted to the original state.

MHSchedule.startDay = 0;

MHSchedule.baseDate = new Date();
MHSchedule.baseDate.setHours(0,0,0,0);
MHSchedule.baseDate.setDate(
		MHSchedule.baseDate.getDate() - (((MHSchedule.baseDate.getDay()-MHSchedule.startDay)+7)%7)
	);

MHSchedule.endDate = new Date(MHSchedule.baseDate.getTime());
MHSchedule.endDate.setDate(MHSchedule.baseDate.getDate()+7);

//alert('baseDate is '+MHSchedule.baseDate.toString()+' and endDate is '+MHSchedule.endDate.toString());
MHSchedule.datePickerConfig = {};
