/*
	 Message display library for the dashboard.
	 update new function for pagniation
	 add note details
	 @author:kada.xingl
	 @version:20110825
	 update code for fix bug 374
	 and code Refactoring by xlin 2011-12-08
 */
var msgRecLength;
var msgSentLength;
var requestTimestamp = 0;
var timestamp = 0;
window.time_Id = null;
window.unreadMsgs = 0;
window.receivedMsgHeight = 0;
window.sentMsgHeight = 0;
window.isFirstLoad = true; //check whether page is load first

Messaging.showUnreadMsgCount = function(count){
	if(count > 1){
		$('#newMsg').html('(You have '+ count +' messages)');
	}else if(count == 1){
		$('#newMsg').html(MESSAGE.DASHBOARD_SHOW_UNREAD_MSGCOUNT_ONE);
	}else{
		$('#newMsg').html('');
	}
}

//main function for received message
Messaging.refreshReceivedMessages = function(showFollowUp, resetStartPage) {
	receivedMsgHeight =  $('#received_messages .receive_td').height();
	$('#received_messages .receive_td').height(receivedMsgHeight);
	$("#receivedNav").hide();
	$('#received_msgs .msg_container').remove();
	Messaging.receivedMsgs_displayLoading();
	
	if (resetStartPage) {
		Messaging.receivedMsgs_settings['start'] = 0;
	}
	
	success = Messaging.AJAX.getReceivedMessages(false, showFollowUp, Messaging.receivedMsgs_settings['start'],0);
}

//auto refresh received messages by xlin
Messaging.autoRefreshReceivedMessages = function(showFollowUp, resetStartPage) {
	if (resetStartPage) {
		Messaging.receivedMsgs_settings['start'] = 0;
	}
	
	success = Messaging.AJAX.getAutoReceivedMessages(false,showFollowUp,0,requestTimestamp);
}

//main method for refresh send message
Messaging.refreshSentMessages = function(showFollowUp, resetStartPage) {
	sentMsgHeight = $('#sent_messages .sent_td').height();
	$('#sent_messages .sent_td').height(sentMsgHeight);
	$('table#sent_msgs tr.msg_container').remove();
	$("#sentNav").hide();
	Messaging.sentMsgs_displayLoading();
	
	if (resetStartPage) {
		Messaging.sentMsgs_settings['start'] = 0;
	}
	
	success = Messaging.AJAX.getSentMessages(false, showFollowUp, Messaging.sentMsgs_settings['start']);
}

//set received msg search options
Messaging.receivedMsgs_setSearchOptions = function(args) {
	if($('#received_resolved_status_true').attr('checked') == true && $('#sent_resolved_status_false').attr('checked')==false){
		args.resolved = 'True';
	}else if($('#received_resolved_status_true').attr('checked') == false && $('#sent_resolved_status_false').attr('checked')==true){
		args.resolved = 'False';
	}else{
		return;
	}
	return args;
}

//set send msg search option and return the args
Messaging.sentMsgs_setSearchOptions = function(args) {
	if($('#snd_resolved_status_true').attr('checked')==true && $('#snd_resolved_status_false').attr('checked')==false){
		args.resolved = 'True';
	}else if($('#snd_resolved_status_true').attr('checked')==false && $('#snd_resolved_status_false').attr('checked')==true){
		args.resolved = 'False';
	}else{
		return;
	}
	return args;
}

//show received msg loading icon
Messaging.receivedMsgs_displayLoading = function() {
	$('table#received_msgs tr.loading').remove(); // Remove the loading message if it's still up.
	var table = $('table#received_msgs');
	$('<tr class="loading"><td class="loading"><img src="/static/img/icons/wait-left.gif" />'+MESSAGE.DASHBOARD_LOADING+'<img src="/static/img/icons/wait-right.gif" /></td></tr>').appendTo(table);
	$('#received_msgs .loading').height($('#received_messages').height() - $('.message_item').height());
}

//show send msg loading icon
Messaging.sentMsgs_displayLoading = function() {
	$('table#sent_msgs tr.loading').remove(); // Remove the loading message if it's still up.
	var table = $('table#sent_msgs');
	$('<tr class="loading"><td class="loading" valign="middle"><img src="/static/img/icons/wait-left.gif" />'+MESSAGE.DASHBOARD_LOADING+'<img src="/static/img/icons/wait-right.gif" /></td></tr>').appendTo(table);
	$('#sent_messages .loading').height($('#sent_messages').height() - $('#sent_msgs .header').height());
}

//show msg info details
Messaging.receivedMsgs_displayMessages = function(showFollowUp,msgRecLength,index,timestamp) {
	
	var msgTalbe = $('#received_msgs');
	
	$('.msg_container',msgTalbe).remove();
	$('tr.loading',msgTalbe).remove();
	
	$("#receivedNav").show();
	if(msgRecLength==0){ //do not recieve any message
		$("#receivedNav").hide();
		$('<tr class="msg_container"><td class="loading">'+MESSAGE.DASHBOARD_NO_MESSAGE+'</td></tr>').appendTo(msgTalbe);
		return;
	}else{ 
		
		// display message items
		Messaging.displayMessageItems(msgTalbe,"sender", Messaging.received_messages,showFollowUp);		
		
		requestTimestamp = timestamp;
		$('#received_messages .receive_td').css({
			'height':'auto'
		});
		var perpage=$("#receivedNav .selectPagePer select").val();
		showReceivePagination(index,perpage,msgRecLength);
	}

	$("div#received_messages table.message_item input:checkbox").unbind('click').click(Messaging.setRecievedMsgResolution);
	$("div#received_messages table.message_item .message_item").unbind('click').click(Messaging.toggleReceivedBody);
}

//received auto msg and show details
Messaging.receivedAutoMsgs_displayMessages = function(showFollowUp,msgRecLength,index,timestamp) {
	if(Messaging.receivedMsgs_settings['start'] == 0){ //just insert them into table for the first page
		msgs = Messaging.received_messages;
		for (var i=msgs.length-1; i>-1; i--) {
			if(checkRevMsgByUUID(msgs[i].id)){
				continue;
			}
			
			var itemObj = Messaging.generateMsgItem("sender", msgs[i], i, showFollowUp);
			
			itemObj.insertBefore($('table#received_msgs .msg_container').eq(0));
		}
		requestTimestamp = timestamp;
		$("div#received_messages table.message_item input:checkbox").unbind('click').click(Messaging.setRecievedMsgResolution);
		$("div#received_messages table.message_item .message_item").unbind('click').click(Messaging.toggleReceivedBody);		
	}
}

//show sent msg info
Messaging.sentMsgs_displayMessages = function(showFollowUp,msgSentLength,index) {
	
	var msgTalbe = $('table#sent_msgs');
	$('tr.msg_container', msgTalbe).remove();
	$('tr.loading', msgTalbe).remove();
	msgs = Messaging.sent_messages;
	$("#sentNav").show();
	if (msgs.length == 0) { //no data get
		$("#sentNav").hide();
		$('<tr class="msg_container"><td class="loading">'+MESSAGE.DASHBOARD_NO_MESSAGE+'</td></tr>').appendTo(msgTalbe);
		return;
	}else{
		
		// display message items
		Messaging.displayMessageItems(msgTalbe,"recipients",msgs,showFollowUp);
		
		$('#sent_messages .sent_td').css({
			'height':'auto'
		});
		var perpage=$("#sentNav .selectPagePer select").val();
		showSentPagination(index,perpage,msgSentLength);
	}
	
	$("div#sent_messages table.message_item input:checkbox").unbind('click').click(Messaging.setSentMsgResolution);
	$("div#sent_messages table.message_item tr.message_item").unbind('click').click(Messaging.toggleSentBody);
}

//show msg items 
Messaging.displayMessageItems = function(msgTable, fromOrToField, msgs, showFollowUp) {
	for (var i=0; i<msgs.length; i++) {
		var showedMsg = msgs[i];
		var itemObj = Messaging.generateMsgItem(fromOrToField, showedMsg, i, showFollowUp);
		itemObj.appendTo(msgTable);
	}
}

//generate msg item
Messaging.generateMsgItem = function(fromOrToField, showedMsg, i, showFollowUp) {
	var followUp = '';
	if (showFollowUp) {
		followUp = '';
	}
	var resolution_flag = '';
	if (showedMsg.resolved) {
		resolution_flag = ' checked ';
	}
	var body_fetched = 0;
	if (showFollowUp) {
		body_fetched = 1;
	}

	var unreadClass = "";
	if (!showedMsg.readStatus) {
		unreadClass = " unread";
	}	

	var itemHtml = '<tr class="msg_container" id="'+i+'">'+
		'<td class="bottom-border">\n\t'+
		'<table class="message_item" id="msg_'+showedMsg.id+'"><tr '+
		'class="msg_item message_item'+unreadClass+'" id="'+showedMsg.id+
		'" body_fetched='+body_fetched+'>\n\t'+
		'<td class="collapse"><a href="javascript:void(0)" class="collapse" id="msg_'+
			showedMsg.id+'_collapse" button_pos=0></a></td>\n\t'+
		'<td class="urgent">';					
	itemHtml +- '<td class="placeholder">&nbsp;</td>';
	if (showedMsg.urgent) {
		itemHtml+='<img src="/static/img/urgent.gif"/>';
	}else{
		itemHtml+='&nbsp;';
	}
	itemHtml += '</td>\n\t' +
			'<td class="attachments">';
	if (showedMsg.attachments&&showedMsg.attachments.length>0) {
		itemHtml+='<img src="/static/img/attachment.png"/>';
	} else {
		itemHtml+='&nbsp;';
	}				
	itemHtml += '</td>\n\t' +	
		'<td class="from">' + showedMsg[fromOrToField]+'</td>\n\t'+
		'<td class="subject">'+'</td>\n\t'+
		'<td class="timestamp">'+showedMsg.timestamp+'</td>\n\t'+
		'<td class="resolution"><input type="checkbox" uuid="'+showedMsg.id+
			'"'+resolution_flag+'/></td>\n\t' +
		//'<td class="placeholder">&nbsp;</td>'+		
		'</tr>'+
		'<tr class="msg_body hidden"><td colspan="8">\n\t'+MESSAGE.DASHBOARD_LOADING+'</td></tr>'+
		
	'</table>\n</tr>';	
	
	var itemObj = $(itemHtml);
	itemObj.find(".subject").html(showedMsg.subject);
	return itemObj;
}

//show info details for recevide body
Messaging.toggleReceivedBody = function(event){
	event.preventDefault();
	
	var msg_id = $(this).attr('id');
	var msg_table = $('table.'+msg_id);
	
	//thiis is fix Mac Firefox jump 
	//$('div#received_messages table#msg_'+msg_id+' tr.msg_body').toggle();
	if($('div#received_messages table#msg_'+msg_id+' tr.msg_body').hasClass('hidden')){
		$('div#received_messages table#msg_'+msg_id+' tr.msg_body').removeClass('hidden');
	}else{
		$('div#received_messages table#msg_'+msg_id+' tr.msg_body').addClass('hidden');
	}
	
	button_position = parseInt($('a#msg_'+msg_id+"_collapse").attr('button_pos'));
	button_position = (button_position+1)%2;
	$('a#msg_'+msg_id+"_collapse").attr('button_pos', button_position);
	
	if($(this).attr('body_fetched')!='1') {
		var args = {'id':msg_id};
		msg = Messaging.received_messages_by_uuid[msg_id];
		Messaging.AJAX.getMessage(msg,msg_id, Messaging.receivedMsgs_toggleBodySuccess, false, $(this));
	}
	
	if($(this).find(".collapse a").attr("button_pos")==1){
		$(this).find(".collapse a").addClass("bgUp");
	}else{
		$(this).find(".collapse a").removeClass("bgUp");
	}
	
	if($(this).hasClass('unread')){
		unreadMsgs--;
	}
	
	Messaging.showUnreadMsgCount(unreadMsgs);
	
	return false;
}

// This function is called by Messaging.AJAX.getMessage on success.
// The purpose of the function is to substitute the loading screen elements
// for the actual content.
// update by kada.xlin 20110908
// add html5 support jPlayer
Messaging.receivedMsgs_toggleBodySuccess = function (msg, args) {
	Messaging.showMsgBody(msg, "received");	
}

//show info details for sent msg
Messaging.toggleSentBody = function(event) {
	event.preventDefault();
	
	var msg_id = $(this).attr('id');
	var msg_table = $('table.'+msg_id);
	
	//$('div#sent_messages table#msg_'+msg_id+' tr.msg_body').toggle();
	if($('div#sent_messages table#msg_'+msg_id+' tr.msg_body').hasClass('hidden')){
		$('div#sent_messages table#msg_'+msg_id+' tr.msg_body').removeClass('hidden');
	}else{
		$('div#sent_messages table#msg_'+msg_id+' tr.msg_body').addClass('hidden');
	}
	
	button_position = parseInt($('a#msg_'+msg_id+"_collapse").attr('button_pos'));
	button_position = (button_position+1)%2;
	$('a#msg_'+msg_id+"_collapse").attr('button_pos', button_position);
	
	if ($(this).attr('body_fetched')!='1') {
		var args = {'id':msg_id};
		msg = Messaging.sent_messages_by_uuid[msg_id];
		Messaging.AJAX.getMessage(msg, msg_id,Messaging.sentMsgs_toggleBodySuccess, false, $(this));
	}
	
	if($(this).find(".collapse a").attr("button_pos")==1){
		$(this).find(".collapse a").addClass("bgUp");
	}else{
		$(this).find(".collapse a").removeClass("bgUp");
	}
	
	return false;
}

//decide browser
function checkBrowser(){
	var Sys = {}; 
    var ua = navigator.userAgent.toLowerCase(); 
    var s; 
    (s = ua.match(/msie ([\d.]+)/)) ? Sys.ie = s[1] : 
    (s = ua.match(/firefox\/([\d.]+)/)) ? Sys.firefox = s[1] : 
    (s = ua.match(/chrome\/([\d.]+)/)) ? Sys.chrome = s[1] : 
    (s = ua.match(/opera.([\d.]+)/)) ? Sys.opera = s[1] : 
    (s = ua.match(/version\/([\d.]+).*safari/)) ? Sys.safari = s[1] : 0;
    return Sys;
}

// This function is called by Messaging.AJAX.getMessage on success.
// The purpose of the function is to substitute the loading screen elements
// for the actual content.
Messaging.sentMsgs_toggleBodySuccess = function (msg, args) {
	Messaging.showMsgBody(msg, "sent");
}

Messaging.showMsgBody = function(msg, msgType) {
	var msgId = msg.id;
	var parentTable = $('div#'+msgType+'_messages table#msg_'+msgId);
	var newBody = '';
	newBody += '	<table class="messageContent"><tr><td class="action">';
	newBody += '		<div class="actionItem"><a href="/FollowUps/Add/Message/'+msgId+'/">'+MESSAGE.DASHBOARD_BTN_CREATE_FOLLOW+'</a></div>';
	newBody += '		<div class="greenIcon actionItem"></div>';
	if (msg.sender_id) {
		newBody += '	<div class="actionItem"><a href="/Messages/New/?user_recipients='+msg.sender_id+'">'+MESSAGE.DASHBOARD_BTN_REPLY+'</a> |</div> ';
		newBody += '	<div class="mailIcon actionItem"></div>';
	}		
	newBody += '	</td></tr></table>';		
	
	// Recipients
	newBody += '	<table class="messageContent">'
			+ '			<tr>'
			+ '				<td class="blank">&nbsp;</td>'
			+ '				<td class="ccsHead">'+MESSAGE.DASHBOARD_LABEL_TO+'</td>'
			+ '<td class="ccs">'
			+ msg.recipients
			+ '</td>'
			+ '			</tr>';
	newBody += '	</table>';		
	
	// CCS
	if (msg.ccs && msg.ccs.length>0) {

		newBody += '	<table class="messageContent">'
				+ '			<tr>'
				+ '				<td class="blank">&nbsp;</td>'
				+ '				<td class="ccsHead">'+MESSAGE.DASHBOARD_LABEL_CCS+'</td>'
				+ '<td class="ccs">'
		$.each(msg.ccs, function(i,n){
				if (i>0) {
					newBody += '; ';
				}
				newBody += n;
		});					
				+ '				</td>'
				+ '			</tr>';
		newBody += '	</table>';		
	}	
	
	// Attachment
	if(msg.attachments && msg.attachments.length>0){
		newBody += '	<table class="messageContent">'
				+ '			<tr>'
				+ '				<td class="blank">&nbsp;</td>'	
				+ '				<td class="attachmentHead">'+MESSAGE.DASHBOARD_LABLE_ATTACHMENTS+':</td>'	
				+ '			</tr>';
		newBody += '	</table>';						
		
		newBody += '	<table class="messageContent"><tr><td>';
		$.each(msg.attachments, function(i, attach){
			newBody += '	<div class="messageContentItem">';
			var attachId = attach["id"];
			newBody += '		<a href="/Messages/'+msgId+'/View/Attachment/'+attachId+'/"';	
			if(isIPad()) {
				newBody += ' target="_blank"';
			}			
			newBody += '>'+interceptString(attach["filename"],30)+'</a> ('+getAttachmentSize(attach["size"])+')';			
			var type = attach["suffix"];
			if (type) {
				type = type.toLowerCase();
			}
			var jPlayerId = msgType+"_"+attachId;
			if(type == 'mp3' || type =='wav'){ //html5 player
				newBody += '<div class="jp_container_outer">';
				newBody += '<div id="jquery_jplayer_'+jPlayerId+'" class="jp-jplayer"></div>';
				newBody += '<div id="jp_container_'+jPlayerId+'" class="jp-audio">';
				newBody += '	<div class="jp-type-single">';
				newBody += '		<div class="jp-gui jp-interface">';
				newBody += '			<ul class="jp-controls">';
				newBody += '				<li><a href="javascript:;" class="jp-play" tabindex="1">'+ MESSAGE.DASHBOARD_LABLE_PLAY+ '</a></li>';
				newBody += '				<li><a href="javascript:;" class="jp-pause" tabindex="1">'+ MESSAGE.DASHBOARD_LABLE_PAUSE +'</a></li>';
				newBody += '				<li><a href="javascript:;" class="jp-stop" tabindex="1">'+ MESSAGE.DASHBOARD_LABLE_STOP +'</a></li>';
				newBody += '				<li><a href="javascript:;" class="jp-mute" tabindex="1" title="'+MESSAGE.DASHBOARD_LABLE_MUTE+'">'+MESSAGE.DASHBOARD_LABLE_MUTE+'</a></li>';
				newBody += '				<li><a href="javascript:;" class="jp-unmute" tabindex="1" title="'+MESSAGE.DASHBOARD_LABLE_UNMUTE+'">'+MESSAGE.DASHBOARD_LABLE_UNMUTE+'</a></li>';
				newBody += '				<li><a href="javascript:;" class="jp-volume-max" tabindex="1" title="'+MESSAGE.DASHBOARD_LABLE_MAX_VOLUME+'">'+MESSAGE.DASHBOARD_LABLE_MAX_VOLUME+'</a></li>';
				newBody += '			</ul>';
				newBody += '			<div class="jp-progress">';
				newBody += '				<div class="jp-seek-bar">';
				newBody += '					<div class="jp-play-bar"></div>';
				newBody += '				</div>';
				newBody += '			</div>';
				newBody += '			<div class="jp-volume-bar">';
				newBody += '				<div class="jp-volume-bar-value"></div>';
				newBody += '			</div>';
				newBody += '			<div class="jp-time-holder">';
				newBody += '				<div class="jp-current-time"></div>';
				newBody += '				<div class="jp-duration"></div>';
				newBody += '				<ul class="jp-toggles">';
				newBody += '					<li><a href="javascript:;" class="jp-repeat" tabindex="1" title="'+MESSAGE.DASHBOARD_LABLE_REPEAT+'">'+MESSAGE.DASHBOARD_LABLE_REPEAT+'</a></li>';
				newBody += '					<li><a href="javascript:;" class="jp-repeat-off" tabindex="1" title="'+MESSAGE.DASHBOARD_LABLE_REPEAT_OFF+'">'+MESSAGE.DASHBOARD_LABLE_REPEAT_OFF+'</a></li>';
				newBody += '				</ul>';
				newBody += '			</div>';
				newBody += '		</div>';
				newBody += '		<div class="jp-no-solution">';
				newBody += '			<span>'+MESSAGE.DASHBOARD_LABLE_UPDATE_REQUIRED+'</span>';
				newBody += 				MESSAGE.DASHBOARD_LABLE_UPDATE_REQUIRED_CONTENT;
				newBody += '				<a href="http://get.adobe.com/flashplayer/" target="_blank" onclick=\'window.open("http://get.adobe.com/flashplayer/");\'>'+MESSAGE.DASHBOARD_LABLE_FLASH_PLUGIN+'</a>.';
				newBody += '		</div>';
				newBody += '	</div>';
				newBody += '</div>';
				newBody += '</div>';
			}			
			newBody += '	</div>';
		});
		newBody += '</td></tr></table>';
	}
	
	// body
	if (msg.body) {
		newBody += '	<table class="messageContent"><tr class="no_background"><td>';		
		newBody += '		<div class="bodycontent">'+'</div>';	
		newBody += '	</td></tr></table>';		
	}
	
	// Answering Service
	newBody += '<table class="messageContent">';
	newBody += '	<tr>';
	newBody += "		<td class='blank'>&nbsp;</td>";		
	newBody += "		<td class='ansHead'>"+MESSAGE.DASHBOARD_LABLE_ANSWERING_SERVICE+":</td>";		
	newBody += '		<td class="ans">';
	if (msg.answering_service) {
		newBody += MESSAGE.DASHBOARD_LABLE_YES;
	} else {
		newBody += MESSAGE.DASHBOARD_LABLE_NO;
	}	
	newBody += '		</td>';
	
	// Callback Number
	if (msg.callback_number) {
		newBody += "	<td class='blank'>&nbsp;</td>";			
		newBody += "	<td class='callbackNumberHead'>"+MESSAGE.DASHBOARD_LABLE_CALLBACK_NUMBER+":</td>"
				+ '		<td class="callbackNumber">'
				+ msg.callback_number
				+ '		</td>';
	} 
	newBody += '		<td>&nbsp;</td>';	 
	newBody += '	</tr>';
	newBody += '</table>';

	// Callback Log
	if (msg.callbacks && msg.callbacks.length>0) {
		newBody += '<table class="messageContent">';
		newBody += '	<tr class="callback_log_title" style="cursor:pointer">';
		newBody += '		<td class="blank">&nbsp;</td>';
		newBody += '		<td class="callbackLogHead">'+MESSAGE.DASHBOARD_LABLE_CALLBACK_LOG+':</td>';
		newBody += '		<td class="callbackLog"><a class="showOrHideCallback hide" href="javascript:void(0)"></a></td>';
		newBody += '	</tr>';	
		newBody += '</table>';
		newBody += '<table class="messageContent" style="display:none;"><tr><td>';		
		newBody += '	<table>'
				+ '			<tr>'
				+ '				<th width="64">&nbsp;</th>'
				+ '				<th width="170">'+MESSAGE.DASHBOARD_LABLE_TIMESTAMP+'</th>'
				+ '				<th>Caller</th>'
				+ '			</tr>';
		$.each(msg.callbacks, function(i,cb){
				newBody += '<tr>'
						+ '		<td>&nbsp;</td>'
						+ '		<td>'+cb.timestamp+'</td>'
						+ '		<td>'+cb.caller_name+'</td>'
						+ '	</tr>';
		});		
		newBody += '	</table>';
		newBody += '</td></tr></table>';		
	}
	$('tr.msg_body td',parentTable).html(newBody);
	
	$('tr.message_item',parentTable).removeClass('unread');
	$('tr#'+msgId, parentTable).attr('body_fetched', 1);
	// display msg body
	parentTable.find(".bodycontent").html(msg.body);
	
	// add event to showOrHideCallback button
	parentTable.find(".callback_log_title").click(function(){
		var jObj = $(this);
		var callbackArea = jObj.closest("table").next();
		var showOrHideBtn = jObj.find(".showOrHideCallback");
		if (showOrHideBtn.hasClass("hide")) {
			callbackArea.show();
			showOrHideBtn.removeClass("hide").addClass("show");
		} else {
			callbackArea.hide();
			showOrHideBtn.removeClass("show").addClass("hide");			
		}
	});	
	
	// add event to jPlayer
	if (msg.attachments && msg.attachments.length>0) {
		$.each(msg.attachments, function(i, attach){
			var attachId = attach["id"];
			var type = attach["suffix"];
			if (type=="mp3" || type=="wav") {
				var jPlayerId = msgType+"_"+attachId;
				var url = "/Messages/" + msgId + "/View/Attachment/" + attachId;
				var param ={};
				switch(type){
					case "wav":
						param = {wav:url + "/.wav"};
						break;
					case "mp3":
						param = {mp3:url + "/.mp3"};
						break;
				}

				$("#jquery_jplayer_"+jPlayerId).jPlayer({
					ready: function () {
						$(this).jPlayer("setMedia",param);				
					},
					play: function() {
						$(this).jPlayer("pauseOthers");
					},
					swfPath: "../../static/js/jPlayer/js/",
					supplied: type,
					cssSelectorAncestor: "#jp_container_"+jPlayerId,
					wmode: 'window',
//					errorAlerts: true,
					error: function(obj) {
						if ('e_url'==obj.jPlayer.error.type) {
							$.ajax({
								url: "/Messages/" + msgId + "/Check/Attachment/" + attachId,
								type: 'GET',
								success: function(data, textStatus, httpRequest) {
									return;
								}, // end success
								error: function(httpRequest, textStatus, errorThrown) {
									alert(MESSAGE.DASHBOARD_LABLE_jPlayer_Alert1
											+ MESSAGE.DASHBOARD_LABLE_jPlayer_Alert2
											+ MESSAGE.DASHBOARD_LABLE_jPlayer_Alert3);
									return;
								}
							});
						}
					}
					//size:fileSize
				});
			}
		});	
	}
}


Messaging.setRecievedMsgResolution = function(event) {
	// Disable the checkbox control (or replace it with a 
	// loading icon or similar
	var msg_id = $(this).attr('uuid');
	var args = {};
	if ($(this).attr('checked')) {
		args['resolved'] = 'True';
		$(this).attr('checked',false)
	}
	else {
		args['resolved'] = 'False';
		$(this).attr('checked',true);
	}
	
	event.preventDefault();
	Messaging.AJAX.updateMessageStatus(msg_id, args);
	return false;
}

//update current received msg status
Messaging.updateReceivedMessageStatus = function(uuid, status_data) {
	if(typeof Messaging.received_messages_by_uuid[uuid] != 'undefined'){
		msg = Messaging.received_messages_by_uuid[uuid];
		// Update the message's status
		msg.resolved = status_data['resolved'];
		
		// Update the message html
		var baseJquerySelector = 'div#received_messages '+	'table#msg_'+uuid;
		if (status_data['resolved']){
			$(baseJquerySelector+' input:checkbox').attr('checked', true);
		}
		else {
			$(baseJquerySelector+' input:checkbox').attr('checked', false);
		}
	}
}

//click send msg tr checkbox function
Messaging.setSentMsgResolution = function(event){
	var msg_id = $(this).attr('uuid');
	var args = {};
	if ($(this).attr('checked')) {
		args['resolved'] = 'True';
		$(this).attr('checked',false)
	}
	else {
		args['resolved'] = 'False';
		$(this).attr('checked',true)
	}
	
	event.preventDefault();
	Messaging.AJAX.updateSentStatus(msg_id, args);
	return false;
}

//update current send msg checkbox 
Messaging.updateSentMessageStatus = function(uuid, status_data) {
		msg = Messaging.received_messages_by_uuid[uuid];
		// Update the message html
		var baseJquerySelector = '#sent_messages '+	'table#msg_'+uuid;
		if (status_data['resolved']){
			$(baseJquerySelector+' input:checkbox').attr('checked', true);
		}
		else {
			$(baseJquerySelector+' input:checkbox').attr('checked', false);
		}
}

//collapse_button_icons = ['ui-icon-plus', 'ui-icon-minus']

//update pagniation old style
function changeStyle(){
	$(".pagniation .prev").html('');
	$(".pagniation .prev").addClass('prevIcon');
	$(".pagniation .next").html('');
	$(".pagniation .next").addClass('nextIcon');
	$('.pagination a').attr({ //add this line to fix the a link jump bug, but there will be a syntax error
	    'href':'javascript:void(0)'
	})
}

//show received msg current page
function showReceivePagination(currentIndex,itemsPerPage,msgRecLength){
	$("#receivedNav .pagniation").pagination(msgRecLength,{
	    callback: receivedCallback,
	    current_page:currentIndex,
	    items_per_page:itemsPerPage,
	    num_edge_entries:1,
	    num_edge_entries: 3,
		num_display_entries: 3,
	    }
	);
	changeStyle();
}

//pagination click one page's callback
function receivedCallback(index,jq){
	if(!startRefreshRequest(1)){
		return false;
	}
	
	Messaging.receivedMsgs_settings['fetch_count']=parseInt($("#receivedNav .selectPagePer select").val());
	Messaging.receivedMsgs_settings['start']=index;
	requestTimestamp = 0;
	unreadMsgs=0;
	Messaging.refreshReceivedMessages();
	changeStyle();
}

//show send msg current page
function showSentPagination(currentIndex,itemsPerPage,msgSentLength){
	$("#sentNav .pagniation").pagination(msgSentLength,{
		callback: sentCallBack,
	    current_page:currentIndex,
	    items_per_page:itemsPerPage,
	    num_edge_entries:1
	    }
	);
	changeStyle();
}

//pagination callback send msg
function sentCallBack(index,jq){
	if(!startRefreshRequest(2)){
		return false;
	}
	
	Messaging.sentMsgs_settings['fetch_count']=$("#sentNav .selectPagePer select").val();
	Messaging.sentMsgs_settings['start']=index;
	Messaging.refreshSentMessages();
	changeStyle();
}

//call this function per 5 minutes
function autoRefresh(){
	Messaging.autoRefreshReceivedMessages();
}

//cilck received refresh button method
function clickReceivedRefresh(){
	if(!startRefreshRequest(1)){
		return false;
	}
	
	startRefreshRequest(1);
	Messaging.receivedMsgs_settings['fetch_count'] = parseInt($("#receivedNav .selectPagePer select").val());
	Messaging.receivedMsgs_settings['start'] = 0;
	unreadMsgs=0; 
	requestTimestamp=0;
	Messaging.refreshReceivedMessages();
	return false;
}

//click send refresh button method
function clickSentRefresh(){
	if(!startRefreshRequest(2)){
		return false;
	}
	startRefreshRequest(2);
	Messaging.sentMsgs_settings['start'] = 0;
	Messaging.sentMsgs_settings['fetch_count'] = parseInt($("#sentNav .selectPagePer select").val());
	Messaging.refreshSentMessages();
	return false;
}

//click rev Resolved checkbox
function cilckRevResolved(){
	if(!startRefreshRequest(1)){
		return false;
	}
	startRefreshRequest(1);
 	unreadMsgs=0;
 	requestTimestamp = 0;
 	Messaging.refreshReceivedMessages(false, true);
}

//click rev unResolved checkbox
function cilckRevUnRevResolved(){
	if(!startRefreshRequest(1)){
		return false;
	}
	startRefreshRequest(1);
	unreadMsgs=0;
	requestTimestamp = 0;
	Messaging.refreshReceivedMessages(false, true);
}

//click snd Resolved checkbox
function cilckSndResolved(){
	if(!startRefreshRequest(2)){
		return false;
	}
	startRefreshRequest(2);
	unreadMsgs=0;
	requestTimestamp = 0;
	Messaging.refreshSentMessages(false, true);
}

//click snd unResolved checkbox
function cilckSndUnRevResolved(){
	if(!startRefreshRequest(2)){
		return false;
	}
	startRefreshRequest(2);
	unreadMsgs=0;
	requestTimestamp = 0;
	Messaging.refreshSentMessages(false, true);
}

$(function(){
	if(typeof $.cookie("recevMsgCount") != "undefined" && $.cookie("recevMsgCount") != null){
		Messaging.receivedMsgs_settings['fetch_count'] = $.cookie("recevMsgCount");
		$("#receivedNav .selectPagePer select").val($.cookie("recevMsgCount"));
	}
	
	if(typeof $.cookie("sndMsgCount") != "undefined" && $.cookie("sndMsgCount") != null){
		Messaging.sentMsgs_settings['fetch_count'] = $.cookie("sndMsgCount");
		$("#sentNav .selectPagePer select").val($.cookie("sndMsgCount"));
	}
	
	Messaging.refreshReceivedMessages();//recevied msg
	Messaging.refreshSentMessages();//send msg
	
	if(time_Id == null){
		time_Id = setInterval('autoRefresh()', autoRefreshTime);
	}
	
	//codereview start the request checker
	setInterval(function(){
		checkRequestTimeout();
	}, 2 * 1000);
	
	$("#receivedNav .selectPagePer select").change(function(){
		if(!startRefreshRequest(1)){
			return false;
		}
		$.cookie("recevMsgCount",$(this).val());
		Messaging.receivedMsgs_settings['fetch_count']=$(this).val();
		Messaging.receivedMsgs_settings['start']=0;
		requestTimestamp = 0;
		unreadMsgs=0;
		Messaging.refreshReceivedMessages();
	});
	
	$("#sentNav .selectPagePer select").change(function(){
		if(!startRefreshRequest(2)){
			return false;
		}
		$.cookie("sndMsgCount", $(this).val());
		Messaging.sentMsgs_settings['start']=0;
	 	Messaging.sentMsgs_settings['fetch_count'] = $(this).val();
	 	Messaging.refreshSentMessages();
	});
	
	$("#received_resolved_status_true").unbind("click").click(function(){
		cilckRevResolved();
	});
	
	$("#sent_resolved_status_false").unbind("click").click(function(){
		cilckRevUnRevResolved();
	});
	
	$('#sent_messages .resolved_status_true').unbind('click').click(function(){
		cilckSndResolved();
	});
	
	$('#sent_messages .resolved_status_false').unbind('click').click(function(){
		cilckSndUnRevResolved();
	});
})

function getAttachmentSize(size) {
	if (!size) {
		return "";
	}
	var ret = "1K";
	var sizeM = size/(1024*1024);
	if (sizeM>=1) {
		return Math.round(sizeM)+"M";
	} else {
		var sizeK = size/1024;
		if (sizeK>=1) {
			return Math.round(sizeK)+"K";
		} else {
			return "1K";
		}
	}
	//var sizer = Math.round(size*1000/(1024*1024))/1000;
	//return sizer < 0.001 ? 0.001 : sizer;
}

//isRcvRequesting means the rcv messages box refresh status true means we are send the request to server and waiting for the response
//isSndRequesting means the snd messages box refresh status true means we are send the request to server and waiting for the response
window.isRcvRequesting = false;
window.isSndRequesting = false;
window.lastRcvRequestTime = 0;
window.lastSndRequestTime = 0;

//We use this function to prevent multiple refresh threads happen
//mode 1=rcv msg 2=send msg
function checkIsRequesting(mode){
	if(mode == 1){
		return isRcvRequesting;
	}else{
		return isSndRequesting;
	}
}

function startRefreshRequest(mode){
	if(checkIsRequesting(mode)){
		return false;
	}
	
	if(mode == 1){
		isRcvRequesting = true;
		lastRcvRequestTime = new Date().getTime();;
	}else{
		isSndRequesting = true;
		lastSndRequestTime = new Date().getTime();;
	}
	
	setResolveButtonsStatus(mode, 0);
	return true;
}

function endRefreshRequest(mode){
	if(mode == 1){
		isRcvRequesting = false;
		lastRcvRequestTime = 0;
	}else{
		isSndRequesting = false;
		lastSndRequestTime = 0;
	}
	
	setResolveButtonsStatus(mode, 1);
}
//Use this function to disable/enable resolve buttons
//mode 1=rcv msg 2=send msg status 1=enable 0 disable
function setResolveButtonsStatus(mode, status){
	var rcvResolvedCheckBox = $('#received_resolved_status_true');
	var rcvUnresolvedCheckBox = $('#sent_resolved_status_false');
	var sndResolvedCheckBox = $('#snd_resolved_status_true');
	var sndUnresolvedCheckBox = $('#snd_resolved_status_false');
	
	if(mode == 1){ //rcv checkbox
		if(status == 1){ //enable click
			rcvResolvedCheckBox.attr({
				'disabled':false
			});
			rcvUnresolvedCheckBox.attr({
				'disabled':false
			});
		}else{ //disable click
			rcvResolvedCheckBox.attr({
				'disabled':true
			});
			rcvUnresolvedCheckBox.attr({
				'disabled':true
			});
		}
	}else{ //snd checkbox
		if(status == 1){ //enable click
			sndResolvedCheckBox.attr({
				'disabled':false
			});
			sndUnresolvedCheckBox.attr({
				'disabled':false
			});
		}else{ //disable click
			sndResolvedCheckBox.attr({
				'disabled':true
			});
			sndUnresolvedCheckBox.attr({
				'disabled':true
			});
		}
	}
}

//a timer to check last send request time. We hard code 30 seconds here
function checkRequestTimeout(){
	var currentTime = new Date().getTime();
	if(lastRcvRequestTime != 0){
		if(currentTime - lastRcvRequestTime > 30 * 1000){
			lastRcvRequestTime = 0;
			endRefreshRequest(1);
			alert(MESSAGE.DASHBOARD_LABLE_CHECKREQUESTTIMEOUT_ALERT);
		}
	}
	
	if(lastSndRequestTime != 0){
		if(currentTime - lastSndRequestTime > 30 * 1000 ){
			lastSndRequestTime = 0;
			endRefreshRequest(2);
			alert(MESSAGE.DASHBOARD_LABLE_CHECKREQUESTTIMEOUT_ALERT);
		}
	}
}

/**
 * check whether msg has exist
 * true:msg exist
 * false:msg not exist
 */
function checkRevMsgByUUID(uuid){
	if(typeof uuid == 'undefined' || uuid == 0 || uuid == ''){
		return false;
	}
	
	var msgLength = Messaging.received_messages.length;

	for(var i = 0; i<msgLength; i++){
		var id = $('#received_msgs .msg_container table').eq(i).attr('id')
		if(uuid == id){
			return true;
		}
	}
	return false;
}
