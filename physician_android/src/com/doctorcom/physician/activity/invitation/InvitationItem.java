package com.doctorcom.physician.activity.invitation;

import java.io.Serializable;

public class InvitationItem implements Serializable {

	/**
	 * 
	 */
	private static final long serialVersionUID = -3940185790935073391L;

	private int id;
	private String recipient, summary;
	private long dueTimestamp;
	public InvitationItem() {
		
	}

	public InvitationItem(int id, String recipient, long dueTimestamp, String summary) {
		this.id = id;
		this.recipient = recipient;
		this.dueTimestamp = dueTimestamp;
		this.summary = summary;
	}
	
	public int getId() {
		return id;
	}

	public void setId(int id) {
		this.id = id;
	}

	public String getRecipient() {
		return recipient;
	}

	public void setRecipient(String recipient) {
		this.recipient = recipient;
	}

	public long getDueTimestamp() {
		return dueTimestamp;
	}

	public void setDueTimestamp(long dueTimestamp) {
		this.dueTimestamp = dueTimestamp;
	}

	public String getSummary() {
		return summary;
	}

	public void setSummary(String summary) {
		this.summary = summary;
	}
}
