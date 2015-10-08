package com.doctorcom.physician.activity.task;

import java.io.Serializable;

public class TaskItem implements Serializable {
	/**
	 * 
	 */
	private static final long serialVersionUID = 2629879605318310799L;
	public static final int TASK_PRIORITY_LOW = 10;
	public static final int TASK_PRIORITY_MIDDLE = 5;
	public static final int TASK_PRIORITY_HIGH = 1;

	private int priority;
	private String note, description;
	private int id;
	private boolean done;
	private long dueTimeStamp;
	
	public int getPriority() {
		return priority;
	}
	public void setPriority(int priority) {
		this.priority = priority;
	}
	public String getNote() {
		return note;
	}
	public void setNote(String note) {
		this.note = note;
	}
	public String getDescription() {
		return description;
	}
	public void setDescription(String description) {
		this.description = description;
	}
	public int getId() {
		return id;
	}
	public void setId(int id) {
		this.id = id;
	}
	public boolean isDone() {
		return done;
	}
	public void setDone(boolean done) {
		this.done = done;
	}
	public long getDueTimeStamp() {
		return dueTimeStamp;
	}
	public void setDueTimeStamp(long dueTimeStamp) {
		this.dueTimeStamp = dueTimeStamp;
	}
}
