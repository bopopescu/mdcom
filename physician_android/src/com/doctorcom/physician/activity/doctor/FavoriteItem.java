package com.doctorcom.physician.activity.doctor;

public class FavoriteItem {
	private String object_name, object_type_display, photo, photo_m,
			prefer_logo;

	private boolean pager_available, call_available, msg_available;
	private int object_id, object_type_flag;

	public String getObject_name() {
		return object_name;
	}

	public void setObject_name(String object_name) {
		this.object_name = object_name;
	}

	public String getObject_type_display() {
		return object_type_display;
	}

	public void setObject_type_display(String object_type_display) {
		this.object_type_display = object_type_display;
	}

	public String getPhoto() {
		return photo;
	}

	public void setPhoto(String photo) {
		this.photo = photo;
	}

	public String getPhoto_m() {
		return photo_m;
	}

	public void setPhoto_m(String photo_m) {
		this.photo_m = photo_m;
	}

	public String getPrefer_logo() {
		return prefer_logo;
	}

	public void setPrefer_logo(String prefer_logo) {
		this.prefer_logo = prefer_logo;
	}

	public boolean isPager_available() {
		return pager_available;
	}

	public void setPager_available(boolean pager_available) {
		this.pager_available = pager_available;
	}

	public boolean isCall_available() {
		return call_available;
	}

	public void setCall_available(boolean call_available) {
		this.call_available = call_available;
	}

	public boolean isMsg_available() {
		return msg_available;
	}

	public void setMsg_available(boolean msg_available) {
		this.msg_available = msg_available;
	}

	public int getObject_id() {
		return object_id;
	}

	public void setObject_id(int object_id) {
		this.object_id = object_id;
	}

	public int getObject_type_flag() {
		return object_type_flag;
	}

	public void setObject_type_flag(int object_type_flag) {
		this.object_type_flag = object_type_flag;
	}

}
