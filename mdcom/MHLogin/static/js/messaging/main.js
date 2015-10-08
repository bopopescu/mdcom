// Messaging library object -- this helps to keep the global namespace clear.
var Messaging = {};
Messaging.received_messages = [];
Messaging.received_messages_by_uuid = {};
Messaging.sent_messages = [];
Messaging.sent_messages_by_uuid = {};

Messaging.Message = function(id, timestamp, readStatus, resolved, sender, recipients, ccs, subject, body, attachments, urgent, refer, thread_uuid, sender_number, last_resolution_timestamp, last_resolved_by) {
	this.body = body;
	this.resolved = resolved;
	this.readStatus = readStatus;
	this.sender = sender;
	this.sender_id = null;
	this.recipients = recipients;
	this.cc_recipients = ccs;
	this.subject = subject;
	this.timestamp = timestamp;
	this.id = id;
	/* Attachments is an array of tuples:
	 * [['uuid-1', 'suffix-1'], ['uuid-2', 'suffix-2'], ...]
	 */
	this.attachments = attachments;
	this.urgent = urgent;
	this.refer = refer;
	this.thread_uuid = thread_uuid;
	this.sender_number = sender_number;
	this.last_resolution_timestamp = last_resolution_timestamp;
	this.last_resolved_by = last_resolved_by;
};

Messaging.clear_received_messages = function() {
	Messaging.received_messages = [];
	//Messaging.received_messages_by_uuid = {};
};
Messaging.clear_sent_messages = function() {
	Messaging.sent_messages = [];
	Messaging.sent_messages_by_uuid = {};
};


Messaging.receivedMsgs_settings = {
	'start': 0,
	'fetch_count': 10,
	'msg_count':0
};
Messaging.sentMsgs_settings = {
	'start': 0,
	'fetch_count': 10,
	'msg_count':0
};
