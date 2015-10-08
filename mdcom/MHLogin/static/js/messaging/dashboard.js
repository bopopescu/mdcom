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
		$('#newMsg').html('(You have '+ count +' unread messages)');
	}else if(count == 1){
		$('#newMsg').html(MESSAGE.DASHBOARD_SHOW_UNREAD_MSGCOUNT_ONE);
	}else{
		$('#newMsg').html('');
	}
};
//add by xlin in 20120525 for bug 582 when new msg receive shing
Messaging.shineNewMsgArrive = function(msgCount){
	if(msgCount==1){
		var msg = 'You have a new message.';
	}else if(msgCount>1){
		var msg = 'You have '+msgCount+' new messages.' ;
	}
	
	doucument.title=msg;
};

Messaging.changeDOMTitle = function(count){
	document.title='';
};

//main function for received message
Messaging.refreshReceivedMessages = function(showFollowUp, resetStartPage) {
	receivedMsgHeight =  $('#received_messages .receive_td').height() - 1; //fix bug 
	$('#received_messages .receive_td').height(receivedMsgHeight);
	$("#receivedNav").hide();
	$('#received_msgs .msg_container').remove();
	Messaging.receivedMsgs_displayLoading();
	
	if (resetStartPage) {
		Messaging.receivedMsgs_settings['start'] = 0;
	}
	
	success = Messaging.AJAX.getReceivedMessages(false, showFollowUp, Messaging.receivedMsgs_settings['start'],0);
};

//auto refresh received messages by xlin
Messaging.autoRefreshReceivedMessages = function(showFollowUp, resetStartPage) {
	if (resetStartPage) {
		Messaging.receivedMsgs_settings['start'] = 0;
	}
	
	success = Messaging.AJAX.getAutoReceivedMessages(false,showFollowUp,0,requestTimestamp);
};

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
};

Messaging.getReceivedMsgsSearchOptions = function() {
	if($('#received_resolved_status_true').attr('checked') == true && $('#sent_resolved_status_false').attr('checked')==false){
		return 'True';
	}else if($('#received_resolved_status_true').attr('checked') == false && $('#sent_resolved_status_false').attr('checked')==true){
		return 'False';
	}else{
		return '';
	}
};

Messaging.getSentMsgsSearchOptions = function() {
	if($('#snd_resolved_status_true').attr('checked')==true && $('#snd_resolved_status_false').attr('checked')==false){
		return 'True';
	}else if($('#snd_resolved_status_true').attr('checked')==false && $('#snd_resolved_status_false').attr('checked')==true){
		return 'False';
	}else{
		return '';
	}
};
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
};

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
};

//show received msg loading icon
Messaging.receivedMsgs_displayLoading = function() {
	$('table#received_msgs tr.loading').remove(); // Remove the loading message if it's still up.
	var table = $('table#received_msgs');
	$('<tr class="loading"><td class="loading"><img src="/static/img/icons/wait-left.gif" />'+MESSAGE.DASHBOARD_LOADING+'<img src="/static/img/icons/wait-right.gif" /></td></tr>').appendTo(table);
	$('#received_msgs .loading').height($('#received_messages').height() - $('#received_messages .header').height());
};

//show send msg loading icon
Messaging.sentMsgs_displayLoading = function() {
	$('table#sent_msgs tr.loading').remove(); // Remove the loading message if it's still up.
	var table = $('table#sent_msgs');
	$('<tr class="loading"><td class="loading" valign="middle"><img src="/static/img/icons/wait-left.gif" />'+MESSAGE.DASHBOARD_LOADING+'<img src="/static/img/icons/wait-right.gif" /></td></tr>').appendTo(table);
	$('#sent_messages .loading').height($('#sent_messages').height() - $('#sent_msgs .header').height());
};

//show msg info details
Messaging.receivedMsgs_displayMessages = function(showFollowUp,msgRecLength,index,timestamp) {
	var msgTalbe = $('#received_msgs');

	$('.msg_container',msgTalbe).remove();
	$('tr.loading',msgTalbe).remove();
	
	$("#receivedNav").show();
	if(msgRecLength==0){ //do not recieve any message
		$("#receivedNav").hide();
		$('<tr class="msg_container"><td class="loading">'+MESSAGE.DASHBOARD_NO_MESSAGE+'</td></tr>').appendTo(msgTalbe);
		//return;
	}else{
		
		// display message items
		Messaging.displayMessageItems(msgTalbe,"sender", Messaging.received_messages,showFollowUp);		
		
		requestTimestamp = timestamp;
		var perpage=$("#receivedNav .selectPagePer select").val();
		showReceivePagination(index,perpage,msgRecLength);
	}
	$('#received_messages .receive_td').css({
		'height':'auto'
	});
	$("div#received_messages table.message_item input:checkbox").unbind('click').click(Messaging.setRecievedMsgResolution);
	$("div#received_messages table.message_item .message_item").unbind('click').click(Messaging.toggleReceivedBody);
};

//TODO add by xlin in 20120528
var notiIndex = 0;
var notiTimeid = null;
Messaging.showNotification = function(){
	var title = MESSAGE.MESSAGE_NOTIFICATION_TEXT;
	
	var len = title.length;
	var str = '';
	if(notiIndex<len){
		str = title.substring(notiIndex, len);
		notiIndex++;
	}else{
		str = title;
		notiIndex=0;
	}
	document.title = str;
	notiTimeid = setTimeout('Messaging.showNotification()',300);
};

Messaging.showNotificationTilte = function(){
	$.ajax({
		url: '/Messages/AJAX/UnreadMsgCount/',
		type: 'GET',
		success: function(data, textStatus, httpRequest) {
			if (textStatus == 'success') {
				data = JSON.parse(data);
				msgRecLength = data['count']
				if(msgRecLength>0){
					clearTimeout(notiTimeid);
					Messaging.showNotification();
					//document.focus();
				} else {
					document.title='DoctorCom';
					clearTimeout(notiTimeid);
				}
			}
		},
		error: function(httpRequest, textStatus, errorThrown) {
		}
	});
}

//received auto msg and show details
Messaging.receivedAutoMsgs_displayMessages = function(showFollowUp,msgRecLength,index,timestamp) {
	//TODO add by xlin in 20120528
	msgs = Messaging.received_messages;
	
	Messaging.showNotificationTilte();

	if(Messaging.receivedMsgs_settings['start'] == 0){ //just insert them into table for the first page
		msgs = Messaging.received_messages;
		for (var i=msgs.length-1; i>-1; i--) {
			if(checkRevMsgByUUID(msgs[i].id)){
				continue;
			}
			checkThreadUUID(msgs[i].thread_uuid);

			var itemObj = Messaging.generateMsgItem("sender", msgs[i], i, showFollowUp);
			$('#received_msgs .msg_container .loading').remove();

			if ($('table#received_msgs .msg_container').length > 0){
				itemObj.insertBefore($('table#received_msgs .msg_container').eq(0));
			} else {
				itemObj.insertAfter($('table#received_msgs .header').eq(0));
			}

			$("#receivedNav").show();
			//comment line 197 by xlin 20120629 that not change page show
			//showReceivePagination(0,10,1);
		}
		requestTimestamp = timestamp;
		$("div#received_messages table.message_item input:checkbox").unbind('click').click(Messaging.setRecievedMsgResolution);
		$("div#received_messages table.message_item .message_item").unbind('click').click(Messaging.toggleReceivedBody);
	}
};

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
		//return;
	}else{
		
		// display message items
		Messaging.displayMessageItems(msgTalbe,"recipients",msgs,showFollowUp);
		
		var perpage=$("#sentNav .selectPagePer select").val();
		showSentPagination(index,perpage,msgSentLength);
	}
	$('#sent_messages .sent_td').css({
		'height':'auto'
	});
	$("div#sent_messages table.message_item input:checkbox").unbind('click').click(Messaging.setSentMsgResolution);
	$("div#sent_messages table.message_item tr.message_item").unbind('click').click(Messaging.toggleSentBody);
};

//show msg items 
Messaging.displayMessageItems = function(msgTable, fromOrToField, msgs, showFollowUp) {
	for (var i=0; i<msgs.length; i++) {
		var showedMsg = msgs[i];
		var itemObj = Messaging.generateMsgItem(fromOrToField, showedMsg, i, showFollowUp);
		itemObj.appendTo(msgTable);
	}
};

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
	
	var trColor = "";
	if(i%2 == 0){
		trColor = " even";
	} else {
		trColor = " odd"; 
	}

	var itemHtml = '<tr class="msg_container" id="'+i+'">'+
		'<td class="bottom-border">\n\t'+
		'<table class="message_item" id="msg_'+showedMsg.id+'" thread_uuid="'+showedMsg.thread_uuid+'"><tr '+
		'class="msg_item message_item'+trColor+unreadClass+'" id="'+showedMsg.id+
		'" body_fetched='+body_fetched+'>\n\t'+
		'<td class="collapse"  style="padding-left:28px"><a href="javascript:void(0)" class="collapse" id="msg_'+
			showedMsg.id+'_collapse" button_pos=0></a></td>\n\t'+
		'<td class="urgent">';					
	if (showedMsg.urgent) {
		itemHtml+='<img src="/static/img/urgent.gif"/>';
	}	
	itemHtml += '</td>\n\t' +
			'<td class="attachments">';					
	if (showedMsg.attachments&&showedMsg.attachments.length>0) {
		itemHtml+='<img src="/static/img/attachment.png"/>';
	} else {
		itemHtml+='&nbsp;';
	}

	var sender_number = '';
	if (showedMsg.sender_number > 1){
		sender_number += ' ('+ showedMsg.sender_number +')';
	}

	itemHtml += '</td>\n\t' +	
		'<td class="from">'+ StrUtils.limitString(showedMsg[fromOrToField],12,'...') + sender_number +'</td>\n\t'+
		'<td class="subject">'+'</td>\n\t'+
		'<td class="timestamp" onmouseout="HideMsgOperationList();" onmouseover="ShowMsgOperationList(this,event);">'+showedMsg.timestamp+''
			+'<div class="msg_popup msg_popup_action_info hide">'
			+'	<table class="msgPopupInfoTable">'
			+'		<tbody><tr>'
			+'			<td class="title">Sent:</td>'
			+'			<td class="content">'+showedMsg.timestamp+'</td>'
			+'		</tr>'
			+ Messaging.renderMessageResolveInfo(showedMsg)
			+ '</tbody></table>'
			+'</div>'
			+'</td>\n\t'+
		'<td class="resolution"><input type="checkbox" uuid="'+showedMsg.id+'"'+resolution_flag+'/></td>\n\t' +
		//'<td class="placeholder">&nbsp;</td>'+		
		'</tr>'+
		Messaging.renderMessageDetailLoading()+
	'</table>\n</tr>';	
	
	var itemObj = $(itemHtml);
	
	if(showedMsg.refer && showedMsg.refer == "NO") {
		itemObj.find(".subject").html("<span style='color:red;'>"+showedMsg.subject+"<span>")
	} else {
		itemObj.find(".subject").html(StrUtils.limitString(showedMsg.subject,30,'...'));
	}
	
	return itemObj;
	
};

/**
 * render message resolveInfo
 * @param {} showedMsg
 * 		showedMsg structure:
 * {
 * 		'resolved': true or false,
 * 		'last_resolution_timestamp': '',
 * 		'last_resolved_by': ''
 * }
 * @return html string
 */
Messaging.renderMessageResolveInfo = function(showedMsg) {
	itemHtml = '';
	if (showedMsg && showedMsg.resolved) {
		itemHtml +='<tr class="resolve_info">'
			+'			<td class="title">Resovled:</td>'
			+'			<td class="content">'+showedMsg.last_resolution_timestamp+'</td>'
			+'		</tr>'
			+'		<tr class="resolve_info">'
			+'			<td class="title">Resovled by:</td>'
			+'			<td class="content">['+showedMsg.last_resolved_by+']</td>'
			+'		</tr>';
	}
	return itemHtml;
};

/**
 * render message detail loading area
 * @return html string
 */
Messaging.renderMessageDetailLoading = function() {
	return '<tr class="msg_body hidden"><td colspan="8" style="color:#000000;">\n\t'+MESSAGE.DASHBOARD_LOADING+'</td></tr>';
};

//show info details for recevide body
Messaging.toggleReceivedBody = function(event){
	//click msg and reset document.title
	document.title='DoctorCom';
	clearTimeout(notiTimeid);
	
	event.preventDefault();
	
	var msg_id = $(this).attr('id');
	var msg_table = $('table.'+msg_id);
	
	//thiis is fix Mac Firefox jump 
	//$('div#received_messages table#msg_'+msg_id+' tr.msg_body').toggle();
	if($('div#received_messages table#msg_'+msg_id+' tr.msg_body').hasClass('hidden')){
		$('div#received_messages table#msg_'+msg_id+' tr.msg_body').removeClass('hidden');
		$('div#received_messages table#msg_'+msg_id).addClass('message_item_show');
		$('div#received_messages table#msg_'+msg_id+' tr.msg_body td').css({'background':'#FFFFFF','padding':'0'});
		$('div#received_messages table#msg_'+msg_id+' tr.msg_body td table#msgPopupInfoTable tr td').css({'padding':'0 10px'});
 		$('div#received_messages table#msg_'+msg_id+' tr.msg_body tr.background1 td').css({'background':'#F3F4F8'});
		$('div#received_messages table#msg_'+msg_id+' tr.msg_body tr.background1 td table tr td').css({'background':'#FFFFFF'});
		// todo - verify. if msg_id is start with number, maybe the selector $('div#received_messages table#msg_'+msg_id+' tr#'+msg_id) return [].
		$('div#received_messages table#msg_'+msg_id+' tr#'+msg_id).addClass('message_item_showbody');
		$('div#received_messages table#msg_'+msg_id+' tr#'+msg_id).closest("td").addClass('message_item_showbody');
	}else{
		$('div#received_messages table#msg_'+msg_id+' tr.msg_body').addClass('hidden');
		$('div#received_messages table#msg_'+msg_id).removeClass('message_item_border');		
		$('div#received_messages table#msg_'+msg_id).removeClass('message_item_show');
		$('div#received_messages table#msg_'+msg_id+' tr#'+msg_id).closest("td").removeClass('message_item_showbody');
		$('div#received_messages table#msg_'+msg_id+' tr#'+msg_id).removeClass('message_item_showbody');
	}

	button_position = parseInt($('a#msg_'+msg_id+"_collapse").attr('button_pos'));
	button_position = (button_position+1)%2;
	$('a#msg_'+msg_id+"_collapse").attr('button_pos', button_position);
	
	if($(this).attr('body_fetched')!='1') {
		var args = {'id':msg_id};
		msg = Messaging.received_messages_by_uuid[msg_id];
		resolved = Messaging.getReceivedMsgsSearchOptions();
		Messaging.AJAX.getMessage(msg,msg_id, "received",Messaging.receivedMsgs_toggleBodySuccess, false, $(this), resolved);
	}
	
	if($(this).find(".collapse a").attr("button_pos")==1){
		$(this).find(".collapse a").addClass("bgUp");
	}else{
		$(this).find(".collapse a").removeClass("bgUp");
	}

	return false;
};

// This function is called by Messaging.AJAX.getMessage on success.
// The purpose of the function is to substitute the loading screen elements
// for the actual content.
// update by kada.xlin 20110908
// add html5 support jPlayer
Messaging.receivedMsgs_toggleBodySuccess = function (msg, args, newBody) {
	Messaging.showMsgBody(msg, "received", newBody);	
};

//show info details for sent msg
Messaging.toggleSentBody = function(event) {
	event.preventDefault();
	
	var msg_id = $(this).attr('id');
	var msg_table = $('table.'+msg_id);
	
	//$('div#sent_messages table#msg_'+msg_id+' tr.msg_body').toggle();
	if($('div#sent_messages table#msg_'+msg_id+' tr.msg_body').hasClass('hidden')){
		$('div#sent_messages table#msg_'+msg_id+' tr.msg_body').removeClass('hidden');
		$('div#sent_messages table#msg_'+msg_id+' tr:first').addClass('message_item_showbody');
		$('div#sent_messages table#msg_'+msg_id+' tr#'+msg_id).closest("td").addClass('message_item_showbody');
		$('div#sent_messages table#msg_'+msg_id).addClass('message_item_show');
		$('div#sent_messages table#msg_'+msg_id+' tr.msg_body td').css({'background':'#FFFFFF','padding':'0'});
		$('div#sent_messages table#msg_'+msg_id+' tr.msg_body td table tr td').css({'background':'#FFFFFF','padding':'0 10px;'});
		$('div#sent_messages table#msg_'+msg_id+' tr.msg_body tr.background1 td').css({'background':'#F3F4F8'});
		$('div#sent_messages table#msg_'+msg_id+' tr.msg_body tr.background1 td table tr td').css({'background':'#FFFFFF'});
	}else{
		$('div#sent_messages table#msg_'+msg_id+' tr.msg_body').addClass('hidden');
		$('div#sent_messages table#msg_'+msg_id).removeClass('message_item_border');		
		$('div#sent_messages table#msg_'+msg_id).removeClass('message_item_show');
		$('div#sent_messages table#msg_'+msg_id+' tr:first').removeClass('message_item_showbody');
		$('div#sent_messages table#msg_'+msg_id+' tr#'+msg_id).closest("td").removeClass('message_item_showbody');
	}
	
	button_position = parseInt($('a#msg_'+msg_id+"_collapse").attr('button_pos'));
	button_position = (button_position+1)%2;
	$('a#msg_'+msg_id+"_collapse").attr('button_pos', button_position);
	
	if ($(this).attr('body_fetched')!='1') {
		var args = {'id':msg_id};
		msg = Messaging.sent_messages_by_uuid[msg_id];
		resolved = Messaging.getSentMsgsSearchOptions();
		Messaging.AJAX.getMessage(msg, msg_id, "sent", Messaging.sentMsgs_toggleBodySuccess, false, $(this), resolved);
	}
	
	if($(this).find(".collapse a").attr("button_pos")==1){
		$(this).find(".collapse a").addClass("bgUp");
	}else{
		$(this).find(".collapse a").removeClass("bgUp");
	}
	
	return false;
};

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
Messaging.sentMsgs_toggleBodySuccess = function (msg, args, newBody) {
	Messaging.showMsgBody(msg, "sent", newBody);
};

Messaging.showMsgBody = function(msg, msgType, newBody) {
	var msgId = msg.id;
	var parentTable = $('div#'+msgType+'_messages table#msg_'+msgId);

	$('tr.msg_body td',parentTable).html(newBody);
	
//	$('tr.message_item',parentTable).removeClass('unread');
	
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
};

UpdateMsgBodyStatus = function(self, isNext, msg_id, is_read, is_sender){
	ChangeMsgBodyStatus(self, isNext);
	UpdateReadStatus(msg_id, is_read, is_sender, self);
	$(self).attr('onclick','').unbind("click").click(function(){
		ChangeMsgBodyStatus(self, isNext);
	});
};

ChangeMsgBodyStatus = function(self,isNext){
	$this = $(self);
	$this.parents('div:first').addClass('hide');
	$this.removeClass('unread');
	if(isNext){
		$this.parents('div:first').next().removeClass('hide');
	} else {
		$this.parents('div:first').prev().removeClass('hide');
	}
};


//FIX ME: htian when modify resolve status 
UpdateReadStatus = function(msg_id, is_read, is_sender, selector){
	if (!is_read){
		if(is_sender=='False'){
			unreadMsgs--;
			Messaging.showUnreadMsgCount(unreadMsgs);
			if(selector){
				$selector = $(selector);
				var len = $selector.parents('#msg_content:first').find('.unread').length;
				if (len == 0){
					$selector.parents('.msg_container:first').find('.unread').removeClass('unread');
				}
			} else {
				var len = $('#'+msg_id).parents('.msg_container:first').find('.unread').length;
				if (len <= 1){
					$('#'+msg_id).removeClass('unread');
				}
			}
		} else {
			if(selector){
				$selector = $(selector);
				var selector_tr = $selector.parents('.msg_container:first').find('tr:first');
				tr_msg_id = $(selector_tr).attr("id");
			
				var len = $('#sent_messages #'+tr_msg_id).parents('.msg_container:first').find('.unread').length;
				if (len <= 1){
					$('#sent_messages').find('#'+tr_msg_id).removeClass('unread');
				}
			} else {
				var len = $('#sent_messages #'+msg_id).parents('.msg_container:first').find('.unread').length;
				if (len <= 1){
					$('#sent_messages').find('#'+msg_id).removeClass('unread');
				}
			}
		}
		var args = {};
		args['read'] = 'True';
		Messaging.AJAX.updateMessageStatus(msg_id, args, function(){});
	}
};

// add event to jPlayer
PlayMsgAttachments = function(attachId,type,msgId){
	if (type=="mp3" || type=="wav") {
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
		$("#jquery_jplayer_"+attachId).jPlayer({
			ready: function () {
				$(this).jPlayer("setMedia",param);				
			},
			play: function() {
				$(this).jPlayer("pauseOthers");
			},
			swfPath: "../../static/js/jPlayer/js/",
			supplied: type,
			cssSelectorAncestor: "#jp_container_"+attachId,
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
		});
	}
};

Messaging.checkAndShow_DicomWindow = function(msg_id, attachment_id, file_name) {
	if (Messaging.checkDicom(msg_id, attachment_id, 1, true, file_name)) {
//		Messaging.show_DicomWindow(msg_id, attachment_id, file_name);
	}
};

Messaging.checkDicom = function(msg_id, attachment_id, count, send_if_not_exist, file_name) {
	data = {};
	if (send_if_not_exist) {
		data["send_if_not_exist"] = true;
	}
	exist = false;
	var max_count = 5;
	var waitId;
	$.comAjax({
		url: '/Messages/'+msg_id+'/CheckDicom/Attachment/'+attachment_id+'/',
		type:'POST',
		data: data,
		async: false,
		success:function(data,txtStatus){
			if (data && data.exist) {
				exist = true;
				Messaging.show_DicomWindow(msg_id, attachment_id, file_name);
			} else {
				if (count < max_count) {
					waitId = $.ui.wait.start(MESSAGE.JQUERY_UI_COMAJAX_MSG_LOAD);
					window.setTimeout(function(){
						exist = Messaging.checkDicom(msg_id, attachment_id, ++count);
						$.ui.wait.stop(waitId);
					}, 1000 );
				} else {
					document.location='/Messages/'+msg_id+'/View/Attachment/'+attachment_id+'/';
				}
			}
		}
	});
	return exist;
};

Messaging.show_DicomWindow = function(msg_id, attachment_id, file_name) {
	var dicom_window_html = '<div id="dicom_window" style="display:none;"><a id="close-dicom" href="javascript:void(0);" ></a>' +
				'<iframe id="dicom_viewer" src="/Messages/'+msg_id+'/ViewDicom/Attachment/'+attachment_id+'/" style="width:760px;height:600px;border:0px;" scrolling="no"></iframe>'
			'</div>';
	$("#dicom_window").remove();
	$('body').append(dicom_window_html);
	var dicom_window = $("#dicom_window").dialog({
			modal:true,
			width:800,
			resizable:false,
//			title: 'Dicom Viewer - '+file_name,
			position:['center',top],
			draggable:false,
			open: function() {
			},
			close:function(){
			}
		});
	$("#dicom_window").dialog('widget').find(".ui-dialog-titlebar").hide();
	$("#close-dicom").click(function(){dicom_window.dialog('close');});
	$("#dicom_window").dialog('widget').find(".ui-widget-content").css('background', 'none repeat scroll 0 0 transparent');
	$("#dicom_window").dialog('widget').css('background', 'none repeat scroll 0 0 transparent');
	$("#dicom_window").dialog('widget').css('border', '0');
	$("#dicom_window").addClass('dcmdialog');
	waitId = $.ui.wait.start(MESSAGE.JQUERY_UI_COMAJAX_MSG_LOAD);
	dicom_window.dialog('open');
	var dicom_viewer = document.getElementById('dicom_viewer');	
	if (!/*@cc_on!@*/0){	//if not IE
		dicom_viewer.onload = function(){
			$("#close-dicom").css("display","block");
			$.ui.wait.stop(waitId);
		};
	} else {
		dicom_viewer.onreadystatechange = function(){
			if (dicom_viewer.readyState == "complete"){
				$("#close-dicom").css("display","block");
				$.ui.wait.stop(waitId);
			}
		};
	}
};

HideMsgOperationList = function(){
	$(".msg_popup").addClass('hide');
};

ShowMsgOperationList = function(self,event){
	$(".msg_popup").addClass('hide');
	$this = $(self).find(".msg_popup");
	$this.removeClass('hide');
	
	if (typeof event.stopPropagation != "undefined") {
		event.stopPropagation();
	} else {
		event.cancelBubble = true;
	}
};

UpdateReferStatusAccept = function(refer_id){
	showSimpleDialog({
		title:"Accept",
		content: "Are you sure you want to accept this referral?",
		width:500,
		dc_buttons: {
			"Yes": {
				'click': function() {
					UpdateReferStatus(refer_id,"AC","");
					$( this ).dialog( "close" );
				},
				'text': 'Yes',
				'class': 'positive-btn'
			},
			"Cancel": function() {
				$( this ).dialog( "close" );
			}
		}
	});
};

UpdateReferStatusRefuse = function(refer_id){
	var html='<div id="referStatusDialog">';
	html += '<div class="text bold">Decline Reason: (Optional)</div>';
	html += '<textarea name="refuse_reason" id="id_refuse_reason" class="refuse_reason"></textarea><br />';
	html += '<div class="text">Are you sure you want to decline this referral?</div>';
	html += '</div>'
	showSimpleDialog({
		title:"Decline",
		content: html,
		width:500,
		height: 280,
		dc_buttons: {
			"Yes": {
				'click': function() {
					var reason = $('#id_refuse_reason').val();
					UpdateReferStatus(refer_id,"RE",reason);
					$( this ).dialog( "close" );
				},
				'text': 'Yes',
				'class': 'positive-btn'
			},
			"Cancel": function() {
				$( this ).dialog( "close" );
			}
		}
	});
};

UpdateReferStatus = function(refer_id,status,refuse_reason){
	$.ajax({
		url: '/Messages/Refer/'+refer_id+'/Update/',
		type: 'GET',
		data: {"status":status,"refuse_reason":refuse_reason},
		success: function(data, httpRequest) {
			$("#refer_status"+refer_id).css("display","none");
			clickReceivedRefresh();
		}, // end success
		error: function(httpRequest, textStatus, errorThrown) {
			alert('An error occurred getting the events.');
			return false;
		}
	});
};

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
};

//update current received msg status
Messaging.updateReceivedMessageStatus = function(uuid, status_data) {
	if(typeof Messaging.received_messages_by_uuid[uuid] != 'undefined'){
		msg = Messaging.received_messages_by_uuid[uuid];
		// Update the message's status
		msg.resolved = status_data['resolved'];
		
		// Update the message html
		var baseJquerySelector = 'div#received_messages '+'table#msg_'+uuid;
		var resolveObj = $(baseJquerySelector+' input:checkbox');
		var oldResolveVal = resolveObj.attr('checked');
		if (status_data['resolved']){
			resolveObj.attr('checked', true);
			if (status_data['read'] && $(baseJquerySelector+' tr#'+uuid).hasClass('unread')){
				$(baseJquerySelector+' tr#'+uuid).removeClass('unread')
				unreadMsgs -= status_data['resolved_read_count'];
				Messaging.showUnreadMsgCount(unreadMsgs);
			}
		}
		else {
			resolveObj.attr('checked', false);
		}
//		//refresh resolve info
//		var message_item_table = $(baseJquerySelector);
//		var msg_item_tr = message_item_table.find("tr.msg_item");
//		var resolve_info_tbody = msg_item_tr.find("td.timestamp table tbody");
//		resolve_info_tbody.find("tr.resolve_info").remove();
//		resolve_info_tbody.append(Messaging.renderMessageResolveInfo(status_data));
//		//refresh message detail
//		var is_open = true;
//		var message_body = message_item_table.find("tr.msg_body");
//		if (message_body.hasClass('hidden')) {
//			is_open = false;
//		}
//		message_body.replaceWith(Messaging.renderMessageDetailLoading());
//		msg_item_tr.attr("body_fetched",0);
//		if (is_open) {
//			msg_item_tr.trigger("click");
//		}
	}
};

//click send msg tr checkbox function
Messaging.setSentMsgResolution = function(event){
	var msg_id = $(this).attr('uuid');
	var args = {};
	if ($(this).attr('checked')) {
		args['resolved'] = 'True';
	}
	else {
		args['resolved'] = 'False';
	}
	event.preventDefault();
	Messaging.AJAX.updateSentStatus(msg_id, args);
	return false;
};

//update current send msg checkbox 
Messaging.updateSentMessageStatus = function(uuid, status_data) {
	// Update the message html
	var baseJquerySelector = '#sent_messages '+'table#msg_'+uuid;
	var resolveObj = $(baseJquerySelector+' input:checkbox');
	var oldResolveVal = resolveObj.attr('checked');
	if (status_data['resolved']){
		resolveObj.attr('checked', true);
	}
	else {
		resolveObj.attr('checked', false);
	}
//	//refresh resolve info
//	var message_item_table = $(baseJquerySelector);
//	var msg_item_tr = message_item_table.find("tr.msg_item");
//	var resolve_info_tbody = msg_item_tr.find("td.timestamp table tbody");
//	resolve_info_tbody.find("tr.resolve_info").remove();
//	resolve_info_tbody.append(Messaging.renderMessageResolveInfo(status_data));
//	//refresh message detail
//	var is_open = true;
//	var message_body = message_item_table.find("tr.msg_body");
//	if (message_body.hasClass('hidden')) {
//		is_open = false;
//	}
//	message_body.replaceWith(Messaging.renderMessageDetailLoading());
//	msg_item_tr.attr("body_fetched",0);
//	if (is_open) {
//		msg_item_tr.trigger("click");
//	}
};

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
		num_display_entries: 5
	});
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
		num_display_entries: 5
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
	//add by xlin in 20120530 to add cleartimeout method
	$(window).click(function(){
		document.title='DoctorCom';
		clearTimeout(notiTimeid);
	});
	
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
});

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
		var id = $('#received_msgs .msg_container table').eq(i).attr('id');
		if('msg_'+uuid == id){
			return true;
		}
	}
	return false;
}

function checkThreadUUID(uuid){
	if(typeof uuid == 'undefined' || uuid == 0 || uuid == ''){
		return false;
	}

	var msgLength = Messaging.received_messages.length;

	$('#received_msgs > tbody > tr.msg_container').each(function(key, value) {
		var $this = $(value)
		var id = $this.find('table[thread_uuid]').attr('thread_uuid');
		if (uuid == id){
			$this.remove();
			return true;
		}
	});

	return false;
}
