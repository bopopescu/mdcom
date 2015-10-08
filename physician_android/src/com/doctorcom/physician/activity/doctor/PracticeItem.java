package com.doctorcom.physician.activity.doctor;

public class PracticeItem {
	private int id;
	private String practiceName, practicePhoto;
	private boolean hasMobile, hasManager,is_favorite;
	public boolean isIs_favorite() {
		return is_favorite;
	}
	public void setIs_favorite(boolean is_favorite) {
		this.is_favorite = is_favorite;
	}
	public int getId() {
		return id;
	}
	public void setId(int id) {
		this.id = id;
	}
	public String getPracticeName() {
		return practiceName;
	}
	public void setPracticeName(String practiceName) {
		this.practiceName = practiceName;
	}
	public String getPracticePhoto() {
		return practicePhoto;
	}
	public void setPracticePhoto(String practicePhoto) {
		this.practicePhoto = practicePhoto;
	}
	public boolean isHasMobile() {
		return hasMobile;
	}
	public void setHasMobile(boolean hasMobile) {
		this.hasMobile = hasMobile;
	}
	public boolean isHasManager() {
		return hasManager;
	}
	public void setHasManager(boolean hasManager) {
		this.hasManager = hasManager;
	}

}
