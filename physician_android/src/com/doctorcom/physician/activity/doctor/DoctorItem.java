package com.doctorcom.physician.activity.doctor;

public class DoctorItem {
	private String practicePhoto, thumbnail, firstName, lastName, specialty,
			fullname, prefer_logo;
	private boolean hasMobile, hasPager, is_favorite;
	private int id;

	public String getFullname() {
		return fullname;
	}

	public void setFullname(String fullname) {
		this.fullname = fullname;
	}

	public boolean isIs_favorite() {
		return is_favorite;
	}

	public void setIs_favorite(boolean is_favorite) {
		this.is_favorite = is_favorite;
	}

	public String getPracticePhoto() {
		return practicePhoto;
	}

	public void setPracticePhoto(String practicePhoto) {
		this.practicePhoto = practicePhoto;
	}

	public String getThumbnail() {
		return thumbnail;
	}

	public void setThumbnail(String thumbnail) {
		this.thumbnail = thumbnail;
	}

	public String getFirstName() {
		return firstName;
	}

	public void setFirstName(String firstName) {
		this.firstName = firstName;
	}

	public String getLastName() {
		return lastName;
	}

	public void setLastName(String lastName) {
		this.lastName = lastName;
	}

	public String getPrefer_logo() {
		return prefer_logo;
	}

	public void setPrefer_logo(String prefer_logo) {
		this.prefer_logo = prefer_logo;
	}

	public String getSpecialty() {
		return specialty;
	}

	public void setSpecialty(String specialty) {
		this.specialty = specialty;
	}

	public boolean isHasMobile() {
		return hasMobile;
	}

	public void setHasMobile(boolean hasMobile) {
		this.hasMobile = hasMobile;
	}

	public boolean isHasPager() {
		return hasPager;
	}

	public void setHasPager(boolean hasPager) {
		this.hasPager = hasPager;
	}

	public int getId() {
		return id;
	}

	public void setId(int id) {
		this.id = id;
	}

}
