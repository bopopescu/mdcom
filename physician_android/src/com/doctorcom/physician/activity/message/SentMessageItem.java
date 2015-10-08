package com.doctorcom.physician.activity.message;

import com.doctorcom.physician.activity.message.ReceivedMessageItem.Attachment;

/**
 * 
 * @author zzhu
 * @version 1.0
 */
public class SentMessageItem {

	static class Recipients {
		private int id;
		private String name;

		public Recipients(int id, String name) {
			this.id = id;
			this.name = name;
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

	static class Body {
		private String id = "";
		private String body = "";
		private Attachment[] attachments = new Attachment[] {};
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

	private Recipients[] recipients;
	private String id, subject, thumbnail, refer;
	private Sender sender;
	private boolean hasAttachements, isRead, isUrgent, isResolved;
	private Body body = new Body();
	private long timeStamp;
	private int threadingCount;
	private String threadingUUID;
	private int actionHistoryCount;

	public Body getBody() {
		return body;
	}

	public void setBody(Body body) {
		this.body = body;
	}

	public Recipients[] getRecipients() {
		return recipients;
	}

	public void setRecipients(Recipients[] recipients) {
		this.recipients = recipients;
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
