
Messaging.AJAX = {};
Messaging.AJAX.HTMLifyText = function(string) {
	// First, convert CRLF to a single character.
	var newString = string.replace(/\r\n/g, '\n');
	// Next, convert 2+ new lines to paragraphs
	newString = newString.replace(/[\r\n]{2,}/g, '</p>\n<p>');
	// Lastly, convert single lines to breaks.
	newString = newString.replace(/[\r\n]/g, '<br />');
	newString = newString.replace(/\t/g, '&nbsp;&nbsp;&nbsp;&nbsp;');
	return newString;
};
Messaging.AJAX.getReceivedMessages = function(get_bodies, showFollowUp,index, timestamp){
	if(time_Id){
		clearInterval(time_Id);
		time_Id = null;
	}
	if(timestamp==0){
		args = {
			offset:Messaging.receivedMsgs_settings['start'],
			count:Messaging.receivedMsgs_settings['fetch_count']
		};
	}else{
		args = {
			timestamp:timestamp
		}
	}
	
	Messaging.receivedMsgs_setSearchOptions(args);
	if (get_bodies) {
		args.get_full = 'True';
	}
	$.ajax({
		url: '/Messages/AJAX/Received/',
		type: 'GET',
		data: args,
		
		success: function(data, textStatus, httpRequest) {
			// Test for success
			if (textStatus == 'success') {
				endRefreshRequest(1);
				Messaging.clear_received_messages();
				allData = JSON.parse(data);
				msgs = allData.msgs;
				for (var idx=0; idx<msgs.length; idx++) {
					Messaging.received_messages[idx] = new Messaging.Message(
									msgs[idx].id, msgs[idx].timestamp,
									msgs[idx].read,
									msgs[idx].resolved, msgs[idx].sender,
									msgs[idx].recipients,
									null, msgs[idx].subject, null,
									msgs[idx].attachments,
									msgs[idx].urgent,
									msgs[idx].refer,
									msgs[idx].thread_uuid,
									msgs[idx].sender_number,
									msgs[idx].last_resolution_timestamp,
									msgs[idx].last_resolved_by
								);
					Messaging.received_messages[idx].sender_id = msgs[idx].sender_id;
					Messaging.received_messages_by_uuid[msgs[idx].id] = Messaging.received_messages[idx];
				}
				Messaging.receivedMsgs_settings['msg_count'] = allData['count'];
				unreadMsgs = allData['unreadMsgs']
				Messaging.showUnreadMsgCount(unreadMsgs);
				if(allData['request_timestamp']==0 || typeof allData['request_timestamp'] =='undefined' || allData['request_timestamp'] ==''){
					alert(MESSAGE.AJAX_MESSAGES_TIMEOUT_ALERT);
				}
				Messaging.receivedMsgs_displayMessages(showFollowUp,allData['count'],index, allData['request_timestamp']);
				if(!time_Id){
					time_Id = setInterval('autoRefresh()', autoRefreshTime);
				}
			}
		}, // end success
		error: function(httpRequest, textStatus, errorThrown) {
			endRefreshRequest(1);
			alert(MESSAGE.AJAX_RECEIVED_MESSAGES_ERROR_ALERT);
			return false;
		}
	});
};

Messaging.AJAX.getAutoReceivedMessages = function(get_bodies, showFollowUp,index, timestamp) {
	if(timestamp==0){
		args = {
			offset:Messaging.receivedMsgs_settings['start'],
			count:Messaging.receivedMsgs_settings['fetch_count']
		};
	}else{
		args = {
			timestamp:timestamp
		}
	}
	Messaging.receivedMsgs_setSearchOptions(args);
	if (get_bodies) {
		args.get_full = 'True';
	}
	$.ajax({
		url: '/Messages/AJAX/Received/',
		type: 'GET',
		data: args,
		
		success: function(data, textStatus, httpRequest) {
			// Test for success
			if (textStatus == 'success') {
				endRefreshRequest(1);
				Messaging.clear_received_messages();
				allData = JSON.parse(data);
				msgs = allData.msgs;
				for (var idx=0; idx<msgs.length; idx++) {
					Messaging.received_messages[idx] = new Messaging.Message(
									msgs[idx].id, msgs[idx].timestamp,
									msgs[idx].read,
									msgs[idx].resolved, msgs[idx].sender, 
									msgs[idx].recipients,
									null, msgs[idx].subject, null,
									msgs[idx].attachments,
									msgs[idx].urgent,
									msgs[idx].refer,
									msgs[idx].thread_uuid,
									msgs[idx].sender_number,
									msgs[idx].last_resolution_timestamp,
									msgs[idx].last_resolved_by
								);
					Messaging.received_messages[idx].sender_id = msgs[idx].sender_id;
					Messaging.received_messages_by_uuid[msgs[idx].id] = Messaging.received_messages[idx];
				}
				Messaging.receivedMsgs_settings['msg_count'] = allData['count'];
				unreadMsgs = allData['unreadMsgs']
				Messaging.showUnreadMsgCount(unreadMsgs);
				if(allData['request_timestamp']==0 || typeof allData['request_timestamp'] =='undefined' || allData['request_timestamp'] ==''){
					alert(MESSAGE.AJAX_MESSAGES_TIMEOUT_ALERT);
				}
				//Messaging.receivedAutoMsgs_displayMessages(showFollowUp,allData['count'],index,allData['request_timestamp'] );
				//var newUnreadMsgCount = allData['msgs'].length;
				var newUnreadMsgCount = allData['unreadMsgs'];
				Messaging.receivedAutoMsgs_displayMessages(showFollowUp,newUnreadMsgCount,index,allData['request_timestamp'] );
			}
		}, // end success
		error: function(httpRequest, textStatus, errorThrown) {
			endRefreshRequest(1);
			//alert(MESSAGE.AJAX_RECEIVED_MESSAGES_ERROR_ALERT);
			return false;
		}
	});
};

Messaging.AJAX.getSentMessages = function(get_bodies, showFollowUp,index) {
	args = {
		offset:Messaging.sentMsgs_settings['start'],
		count:Messaging.sentMsgs_settings['fetch_count']
	};
	Messaging.sentMsgs_setSearchOptions(args);
	if (get_bodies) {
		args.get_full = 'True';
	}
	$.ajax({
		url: '/Messages/AJAX/Sent/',
		type: 'GET',
		data: args,
		
		success: function(data, textStatus, httpRequest) {
			// Test for success
			if (textStatus == 'success') {
				endRefreshRequest(2);
				Messaging.clear_sent_messages();
				var allData = JSON.parse(data);
				msgs = allData.msgs;
				msgSentLength=allData.count;
				for (var idx=0; idx<msgs.length; idx++) {
					Messaging.sent_messages[idx] = new Messaging.Message(
									msgs[idx].id, msgs[idx].timestamp,
									msgs[idx].read,
									msgs[idx].resolved, null,
									msgs[idx].recipients, msgs[idx].ccs,
									msgs[idx].subject, null, msgs[idx].attachments,
									msgs[idx].urgent,
									msgs[idx].refer,
									msgs[idx].thread_uuid,
									msgs[idx].sender_number,
									msgs[idx].last_resolution_timestamp,
									msgs[idx].last_resolved_by
								);
					Messaging.sent_messages_by_uuid[msgs[idx].id] = Messaging.sent_messages[idx];
				}
			}
			Messaging.sentMsgs_settings['msg_count'] = allData['count'];
			msgSentLength = allData['count'];
			Messaging.sentMsgs_displayMessages(showFollowUp,msgSentLength,index);
			
		}, // end success
		error: function(httpRequest, textStatus, errorThrown) {
			endRefreshRequest(2);
			alert(MESSAGE.AJAX_SENT_MESSAGES_ERROR_ALERT);
			return false;
		}
	});
};
Messaging.AJAX.getMessage = function(msg, id, type,success, failure, args, resolved) {
	$.ajax({
		url: '/Messages/AJAX/'+id+'/'+type+'/',
		type: 'GET',
		data:{'resolved':resolved},
		success: function(data, textStatus, httpRequest) {
			return success(msg, args, data);
			data = JSON.parse(data);
			if(data){
				msg.body = data['body'];
				msg.callback_number = data['callback_number'];
				msg.callbacks = data['callbacks'];
				msg.urgent = data['urgent'];
				msg.answering_service = data['answering_service'];
				msg.attachments = data['attachments'];
				msg.ccs = data['ccs'];
				msg.refer = data['refer']
				
				if (msg.body == null) {
					msg.body = MESSAGE.AJAX_GET_MESSAGE_BODY1 + msg.id + MESSAGE.AJAX_GET_MESSAGE_BODY2;
				}
				msg.read = true;
				
			}else{
				alert(MESSAGE.AJAX_GET_MESSAGE_ERROR_ALERT);
				location.reload(true);
			}
		}, // end success
		error: function(httpRequest, textStatus, errorThrown) {
			alert(MESSAGE.AJAX_GET_MESSAGE_ERROR_ALERT);
			location.reload(true);
		}
	});
};

Messaging.AJAX.updateMessageStatus = function(id, args) {
	$.comAjax({
		url: '/Messages/AJAX/'+id+'/Update/',
		type: 'GET',
		data: args,
		success: function(data, textStatus, httpRequest) {
			msg = JSON.parse(data);
			if (msg['success'] == 'True') {
				// Clean up the returned data.
				Messaging.updateReceivedMessageStatus(id, msg['data']);
			}
		}, // end success
		error: function(httpRequest, textStatus, errorThrown) {
			alert(MESSAGE.AJAX_UPDATE_MESSAGE_ERROR_ALERT);
			return false;
		}
	});
};

Messaging.AJAX.updateSentStatus = function(id, args) {
	$.comAjax({
		url: '/Messages/AJAX/'+id+'/Update/',
		type: 'GET',
		data: args,
		success: function(data, textStatus, httpRequest) {
			msg = JSON.parse(data);
			if (msg['success'] == 'True') {
				// Clean up the returned data.
				//Messaging.updateReceivedMessageStatus(id, msg['data']);
				Messaging.updateSentMessageStatus(id, msg['data']);
			}
		}, // end success
		error: function(httpRequest, textStatus, errorThrown) {
			alert(MESSAGE.AJAX_UPDATE_MESSAGE_ERROR_ALERT);
			return false;
		}
	});
};

Messaging.AJAX.errorReport = function(error) {

};
Messaging.AJAX.warningReport = function(warning) {

};
