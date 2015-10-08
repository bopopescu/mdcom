$(function(){
	initValidationPage();
	var pf = $('#profile_form').validate({
		rules:{
			first_name:{required:true},
			last_name:{required:true},
			email:{required:true,email:true},
			gender:{required:true},
			mobile_phone:{required:mobile_required,isPhone:true},
			office_phone:{isPhone:true},
			phone:{isPhone:true},
			pager:{isPhone:true},
			address1:{required:true},
			city:{required:true},
			state:{required:true},
			zip:{required:true, isZipCode:true}
		},
		messages:{
			first_name: MESSAGE.PROFILE_FIRST_NAME_REQUIRED,
			last_name: MESSAGE.PROFILE_LAST_NAME_REQUIRED,
			email:{
				required: MESSAGE.PROFILE_EMAIL_REQUIRED,
				email: MESSAGE.PROFILE_EMAIL_NOT_VALID
			},
			gender: {
				required:MESSAGE.PROFILE_GENDER_REQUIRED
			},
			mobile_phone:{
				required: MESSAGE.PROFILE_MOBILE_PHONE_REQUIRED,
				isPhone: MESSAGE.PROFILE_MOBILE_PHONE_NOT_VALID
			},
			office_phone:{
				isPhone: MESSAGE.PROFILE_OFFICE_PHONE_NOT_VALID
			},
			phone:{
				isPhone: MESSAGE.PROFILE_OTHER_PHONE_NOT_VALID
			},
			pager:{
				isPhone: MESSAGE.PROFILE_PAGER_NOT_VALID
			},
			address1: MESSAGE.PROFILE_ADDRESS1_REQUIRED,
			city: MESSAGE.PROFILE_CITY_REQUIRED,
			state: MESSAGE.PROFILE_STATE_REQUIRED,
			zip: {
				required: MESSAGE.PROFILE_ZIP_REQUIRED,
				isZipCode: MESSAGE.PROFILE_ZIP_NOT_VALID
			}
		},
		showErrors: showErrorsBelow,
		submitHandler:function(form){
			var user = getProfileContactInfo({
					"email":$("#id_email").val(),
					"mobile_phone":$("#id_mobile_phone").val(),
					"pager":$("#id_pager").val()
				});
			if (!user) {
				alert(MESSAGE.PROFILE_GET_USER_SERVER_ERROR);
				return false;
			}
			if (!uniqueCheck(user)) {
				return false;
			}
			verifyCheck(user);
			executeValidateChain(
				generateValidateChain(user), form, false, 
				function(type){
					setValidateStatus(type);
				}
			);
		}
	});
});

function initValidationPage() {
	$(".redstar").remove();
	$('#id_first_name, #id_last_name, #id_gender, #id_email, #id_address1, #id_city, #id_state, #id_zip').after('<span class="redstar">*</span>');
	if (mobile_required) {
		$("#id_mobile_phone").after('<span class="redstar">*</span>');
	}
	setValidateStatus("email");
	setValidateStatus("mobile_phone");
	setValidateStatus("pager");
}

function verifyCheck(user) {
	changeConfirmedByNewValue(user, "email");
	changeConfirmedByNewValue(user, "mobile_phone");
	changeConfirmedByNewValue(user, "pager");
}

function changeConfirmedByNewValue(user, type) {
	var confirmed_field = Validate_Configs[type]["confirmed_field"];
	var newVal = $("#id_"+type).val();
	if (!newVal || needValidate(user, type)) {
		$('#id_'+confirmed_field).val("False");
	} else {
		$('#id_'+confirmed_field).val("True");
	}
	setValidateStatus(type);
}

$(function() {
	$("textarea[maxlength]").keyup(function() {
	var area = $(this);
	var max = parseInt(area.attr("maxlength"), 10);
	if (max > 0) {
		if (area.val().length > max) {
			area.val(area.val().substr(0, max));
		}
	}
});
	$("textarea[maxlength]").blur(function() {
		var area = $(this);
		var max = parseInt(area.attr("maxlength"), 10);
		if (max > 0) {
			if (area.val().length > max) {
				area.val(area.val().substr(0, max));
			}
		}
	});
});
