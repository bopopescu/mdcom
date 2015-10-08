$(function(){
	initValidationPage();
	var pf = $('#profile_form').validate({
		rules:{
			email:{required:true,email:true},
			mobile_phone:{required:mobile_required,isPhone:true},
			pager:{isPhone:true}
		},
		messages:{
			email:{
				required: MESSAGE.PROFILE_EMAIL_REQUIRED,
				email: MESSAGE.PROFILE_EMAIL_NOT_VALID
			},
			mobile_phone:{
				required: MESSAGE.PROFILE_MOBILE_PHONE_REQUIRED,
				isPhone: MESSAGE.PROFILE_MOBILE_PHONE_NOT_VALID
			},
			pager:{
				isPhone: MESSAGE.PROFILE_PAGER_NOT_VALID
			}
		},
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
			executeValidateChain(
				generateValidateChain(user), form, true, 
				function(type){
					setValidateStatus(type, true);
				}
			);
		}
	});
});

function initValidationPage() {
	$(".redstar").remove();
	$('#id_email').after('<span class="redstar">*</span>');
	if (mobile_required) {
	 	$('#id_mobile_phone').after('<span class="redstar">*</span>');
	}
	setValidateStatus("email", true);
	setValidateStatus("mobile_phone", true);
	setValidateStatus("pager", true);
}
