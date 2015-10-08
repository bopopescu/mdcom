package com.doctorcom.physician.activity.doctor;

public class DoctorTabItem {
	public static final int PROVIDER = 1, STAFF = 1 << 1,
			LOCAL_PRACTICEE = 1 << 2, ORG = 1 << 3, FAVOURITE = 1 << 4;

	private int resultType = ORG;
	private String id, name, logo, url, logo_middle;
	private boolean isSelected = false;

	public DoctorTabItem() {

	}

	public DoctorTabItem(String id, String name, String logo, String url,
			int resultType) {
		this.id = id;
		this.name = name;
		this.logo = logo;
		this.url = url;
		this.resultType = resultType;
	}

	public DoctorTabItem(String id, String name, String logo, String url,
			int resultType, boolean isSelected) {
		this.id = id;
		this.name = name;
		this.logo = logo;
		this.url = url;
		this.resultType = resultType;
		this.isSelected = isSelected;
	}

	public String getId() {
		return id;
	}

	public void setId(String id) {
		this.id = id;
	}

	public String getName() {
		return name;
	}

	public void setName(String name) {
		this.name = name;
	}

	public String getLogo() {
		return logo;
	}

	public void setLogo(String logo) {
		this.logo = logo;
	}

	public String getUrl() {
		return url;
	}

	public void setUrl(String url) {
		this.url = url;
	}

	public String getLogo_middle() {
		return logo_middle;
	}

	public void setLogo_middle(String logo_middle) {
		this.logo_middle = logo_middle;
	}

	public int getResultType() {
		return resultType;
	}

	public void setResultType(int resultType) {
		this.resultType = resultType;
	}

	public boolean isSelected() {
		return isSelected;
	}

	public void setSelected(boolean isSelected) {
		this.isSelected = isSelected;
	}

}
