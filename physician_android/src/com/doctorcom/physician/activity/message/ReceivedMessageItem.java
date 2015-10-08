package com.doctorcom.physician.activity.message;


/**
 * 
 * @author zzhu
 * @version 1.0
 */
public class ReceivedMessageItem {

	static class Sender {
		private int id;
		private String name;
		private String photo;

		public String getPhoto() {
			return photo;
		}

		public void setPhoto(String photo) {
			this.photo = photo;
		}

		public int getId() {
			return id;
		}

		public void setId(int id) {
			this.id = id;
		}

		public String getName() {
			return name;
		}

		public void setName(String name) {
			this.name = name;
		}
	}
	
	static class Attachment{
		private String id;
		private String filename;
		private long filesize;
		public String getId() {
			return id;
		}
		public void setId(String id) {
			this.id = id;
		}
		public String getFilename() {
			return filename;
		}
		public void setFilename(String filename) {
			this.filename = filename;
		}
		public long getFilesize() {
			return filesize;
		}
		public void setFilesize(long filesize) {
			this.filesize = filesize;
		}
	}
	
	static class Body {
		private String id = "";
		private String body = "";
		private Attachment[] attachments = new Attachment[]{};
		private String jsonStrMessageDetail;

		public String getJsonStrMessageDetail() {
			return jsonStrMessageDetail;
		}

		public void setJsonStrMessageDetail(String jsonStrMessageDetail) {
			this.jsonStrMessageDetail = jsonStrMessageDetail;
		}

		public Attachment[] getAttachments() {
			return attachments;
		}

		public void setAttachments(Attachment[] attachments) {
			this.attachments = attachments;
		}

		public String getId() {
			return id;
		}

		public void setId(String id) {
			this.id = id;
		}

		public String getBody() {
			return body;
		}

		public void setBody(String body) {
			this.body = body;
		}
	}


	private String id, subject, thumbnail, refer, message_type, callback_number;
	private Sender sender;
	private Body body = new Body();
	private boolean hasAttachements, isRead, isUrgent, isResolved;
	private long timeStamp;
	private int threadingCount;
	private String threadingUUID;
	private String isPlaying;
	private int actionHistoryCount;	

	public String getIsPlaying() {
		return isPlaying;
	}

	public void setIsPlaying(String isPlaying) {
		this.isPlaying = isPlaying;
	}
	
	public String getCallback_number() {
		return callback_number;
	}

	public void setCallback_number(String callback_number) {
		this.callback_number = callback_number;
	}

	public int getActionHistoryCount() {
		return actionHistoryCount;
	}

	public void setActionHistoryCount(int actionHistoryCount) {
		this.actionHistoryCount = actionHistoryCount;
	}

	public String getId() {
		return id;
	}

	public void setId(String id) {
		this.id = id;
	}

	public String getSubject() {
		return subject;
	}

	public void setSubject(String subject) {
		this.subject = subject;
	}

	public Body getBody() {
		return body;
	}

	public void setBody(Body body) {
		this.body = body;
	}

	public String getThumbnail() {
		return thumbnail;
	}

	public void setThumbnail(String thumbnail) {
		this.thumbnail = thumbnail;
	}

	public Sender getSender() {
		return sender;
	}

	public void setSender(Sender sender) {
		this.sender = sender;
	}

	public boolean isHasAttachements() {
		return hasAttachements;
	}

	public void setHasAttachements(boolean hasAttachements) {
		this.hasAttachements = hasAttachements;
	}

	public boolean isRead() {
		return isRead;
	}

	public void setRead(boolean isRead) {
		this.isRead = isRead;
	}

	public String getRefer() {
		return refer;
	}

	public void setRefer(String refer) {
		this.refer = refer;
	}
	
	public String getMessage_type() {
		return message_type;
	}

	public void setMessage_type(String message_type) {
		this.message_type = message_type;
	}

	public boolean isUrgent() {
		return isUrgent;
	}

	public void setUrgent(boolean isUrgent) {
		this.isUrgent = isUrgent;
	}

	public long getTimeStamp() {
		return timeStamp;
	}

	public void setTimeStamp(long timeStamp) {
		this.timeStamp = timeStamp;
	}

	public int getThreadingCount() {
		return threadingCount;
	}

	public void setThreadingCount(int threadingCount) {
		this.threadingCount = threadingCount;
	}

	public String getThreadingUUID() {
		return threadingUUID;
	}

	public void setThreadingUUID(String threadingUUID) {
		this.threadingUUID = threadingUUID;
	}

	public boolean isResolved() {
		return isResolved;
	}

	public void setResolved(boolean isResolved) {
		this.isResolved = isResolved;
	}

}
