var Validate_Configs={
	'email': {
		'title': MESSAGE.VALIDATE_DIALOG_EMAIL_TITLE,
		'received_text': MESSAGE.VALIDATE_DIALOG_EMAIL_RECEIVED_TEXT,
		'send_url': '/Validations/SendCode/',
		'validate_url': '/Validations/Validate/',
		'send_type': '1',
		'confirmed_field': 'email_confirmed'
	},
	'mobile_phone': {
		'title': MESSAGE.VALIDATE_DIALOG_MOBILE_PHONE_TITLE,
		'received_text': MESSAGE.VALIDATE_DIALOG_MOBILE_PHONE_RECEIVED_TEXT,
		'send_url': '/Validations/SendCode/',
		'validate_url': '/Validations/Validate/',
		'send_type': '2',
		'confirmed_field': 'mobile_confirmed'
	},
	'pager': {
		'title': MESSAGE.VALIDATE_DIALOG_PAGER_TITLE,
		'received_text': MESSAGE.VALIDATE_DIALOG_PAGER_RECEIVED_TEXT,
		'send_url': '/Validations/SendCode/',
		'validate_url': '/Validations/Validate/',
		'send_type': '3',
		'confirmed_field': 'pager_confirmed'
	}
};

function getProfileContactInfo(data) {
	var userProfile = null;
	$.comAjax({
		type:'GET',
		url: '/Validations/ContactInfo/',
		data: data,
		async: false,
		success:function(data, status){
			if(status=='success'){
				userProfile = data["user"];
			}
		},
		error:function(data, status){
			alert(MESSAGE.PROFILE_GET_USER_SERVER_ERROR);
		}
	});
	return userProfile;
}

function uniqueCheck(user) {
	var ret = true;
	if (user) {
		if (!BoolUtils.str2bool(user.email_unique)) {
			$('#id_email').addClass('error');
			$('#id_email').after('<label for="id_email" generated="true" class="error">'+MESSAGE.PROFILE_EMAIL_EXISTS+'</label>');
			ret = false;
		}
		if (!BoolUtils.str2bool(user.mobile_phone_unique)) {
			$('#id_mobile_phone').addClass('error');
			$('#id_mobile_phone').after('<label for="id_mobile_phone" generated="true" class="error">'+MESSAGE.PROFILE_MOBILE_PHONE_EXISTS+'</label>');
			ret = false;
		}
	}
	return ret;
}

function generateValidateChain(user) {
	var email_validate = {
		"check": function() {
			return needValidate(user, "email");
		},
		"process": function(obj, form, noSkip, afterValidate) {
			showValidateDialog("email", obj, form, noSkip, afterValidate);
		},
		"next": false
	};

	var pager_validate = {
		"check": function() {
			return needValidate(user, "pager") && Constant.CALL_ENABLE;
		},
		"process": function(obj, form, noSkip, afterValidate) {
			showValidateDialog("pager", obj, form, noSkip, afterValidate);
		},
		"next": email_validate
	};

	var mobile_validate = {
		"check": function() {
			return needValidate(user, "mobile_phone") && Constant.CALL_ENABLE;
		},
		"process": function(obj, form, noSkip, afterValidate) {
			showValidateDialog("mobile_phone", obj, form, noSkip, afterValidate);
		},
		"next": pager_validate
	};
	return mobile_validate;
}

function executeValidateChain(obj, form, noSkip, afterValidate) {
	if (!obj) {
		form.submit();
		$('input[type="submit"]').attr("disabled", "disabled").css("cursor","default");
		return;
	}
	var c = obj["check"]();
	if (c) {
		obj["process"](obj, form, noSkip, afterValidate);
	} else {
		executeValidateChain(obj["next"], form, noSkip, afterValidate);
	}
}

function needValidate(user, type) {
	var newVal = $("#id_"+type).val();
	newVal = StrUtils.parsePhoneNumber(newVal);
	var confirmed = user[Validate_Configs[type]["confirmed_field"]];
	var persistVal = user[type];
	if ((newVal && newVal != persistVal) || (newVal && !confirmed)) {
		return true;
	} else {
		return false;
	}
}

function showValidateDialog(type, obj, form, noSkip, afterValidate){
	var Validate_Config = Validate_Configs[type];
	var inputObj = $("#id_"+type);
	var val = inputObj.val();

	var send_type = Validate_Config['send_type'];
	if (send_type && send_type != "1") {
		val = StrUtils.parsePhoneNumber(val);
	}

	$('#validationDialog').dialog({
		title: MESSAGE.VALIDATE_DIALOG_LABEL_VALIDATE + " " + Validate_Config['title'],
		width:480,
		modal:true,
		resizable:false,
		draggable:false,
		open: function(){
			var html = '';
			html += '<div class="content">';
			html += '<div id="send_info" class="row1">';
			html += MESSAGE.VALIDATE_DIALOG_SEND_INFO_SUCCESS1 + Validate_Config['received_text'] + MESSAGE.VALIDATE_DIALOG_SEND_INFO_SUCCESS2;
			if (Constant.SEND_CODE_WAITING_TIME > 1) {
				html += Constant.SEND_CODE_WAITING_TIME + MESSAGE.VALIDATE_DIALOG_SEND_INFO_SUCCESS3;
			} else {
				html += Constant.SEND_CODE_WAITING_TIME + MESSAGE.VALIDATE_DIALOG_SEND_INFO_SUCCESS4;
			}
			
			html += MESSAGE.VALIDATE_DIALOG_SEND_INFO_SUCCESS5;
			html += '</div>';

			html += '<div class="row">';
			html += '	<div class="cell left">'+Validate_Config['title']+':</div>';
			html += '	<div class="cell">'+val+'</div>';
			html += '</div>';

			html += '<div class="row">';
			html += '	<div class="cell left">'+MESSAGE.VALIDATE_DIALOG_LABEL_VALIDATION_CODE+':</div>';
			html += '	<div class="cell"><input id="validate_code_input" type="text" maxlength="4"/></div>';
			html += '</div>';

			html += '<div id="validate_info" class="error">';
			html += '</div>';

			html += '</div>';

			html += '<div class="line"></div>';
			html += '<div id="action_area" class="buttons">';
			html += '	<div id="send_code_btn" class="button_long_disabled" disabled="disabled">'+MESSAGE.VALIDATE_DIALOG_LABEL_RESEND+'<span id="time_info"></span></div>';
			html += '	<div id="validate_code_btn" class="button positive_button">'+MESSAGE.VALIDATE_DIALOG_LABEL_VALIDATE+'</div>';
			html += '	<div id="cancel_btn" class="button">'+MESSAGE.VALIDATE_DIALOG_LABEL_CANCEL+'</div>';
			html += '	<div id="skip_btn" class="button" style="display:none;" title="'+MESSAGE.VALIDATE_DIALOG_TIP_SKIP+'">'+MESSAGE.VALIDATE_DIALOG_LABEL_SKIP+'</div>';
			html += '</div>';

			$(this).html(html);

			sendCode("init");
			adjustButtonArea($('#validationDialog'));
			$('#send_code_btn').click(function(){
				if ($(this).attr("disabled")) {
					return false;
				}
				$("#validate_info").text("");
				$("#validate_code_input").val("");
				removeValidateTimer();
				sendCode();
			});
			
			$('#validate_code_input').change(function(){
				$("#validate_info").text("");
			});

			$('#validate_code_btn').click(function(){
				if ($(this).attr("disabled")) {
					return false;
				}

				var code = $("#validate_code_input").val();
				if (!code) {
					$("#validate_info").text(MESSAGE.VALIDATE_DIALOG_VALIDATE_INFO_REQUIRED);
					return;
				}
				if (isNaN(code) || code.length!=4) {
					$("#validate_info").text(MESSAGE.VALIDATE_DIALOG_VALIDATE_INFO_FORMAT);
					return;
				}
				$.comAjax({
					url: Validate_Config['validate_url'],
					type:'POST',
					data:{
						code : code,
						recipient : val,
						type : send_type
					},
					success:function(data,txtStatus){
						if (data && data.flag==0) {
							$('#id_'+Validate_Config['confirmed_field']).val("True");
							$('#validationDialog').dialog("close");
							if (afterValidate) {
								afterValidate(type);
							}
							alert(MESSAGE.VALIDATE_DIALOG_VALIDATE_INFO_SUCCESS1+Validate_Config['received_text']+MESSAGE.VALIDATE_DIALOG_VALIDATE_INFO_SUCCESS2);
							executeValidateChain(obj["next"], form, noSkip, afterValidate);
						} else if (data.flag==1){
							$("#validate_info").text(MESSAGE.VALIDATE_DIALOG_VALIDATE_INFO_NOT_APPLY);
						} else if (data.flag==2){
							$("#validate_info").text(MESSAGE.VALIDATE_DIALOG_VALIDATE_INFO_INCORRECT);
						} else if (data.flag==3){
							setValidateButtonLocked(true);
						} else if (data.flag==4){
							$("#validate_info").text(MESSAGE.VALIDATE_DIALOG_VALIDATE_INFO_OVERDUE);
						}
					},
					error:function(data,txtStatus){
						alert(MESSAGE.VALIDATE_DIALOG_VALIDATE_SERVER_ERROR);
					}
				});
			});

			$('#cancel_btn').click(function(){
				$('#validationDialog').dialog("close");
			});

			$('#skip_btn').click(function(){
				$('#id_'+Validate_Config['confirmed_field']).val("False");
				setValidateStatus(type);
				$('#validationDialog').dialog("close");
				executeValidateChain(obj["next"], form, noSkip, afterValidate);
			});
		},
		close: function() {
			removeValidateTimer();
		}
	});
	
	function sendCode(isInit) {
		$.comAjax({
			url: Validate_Config['send_url'],
			type:'POST',
			data:{
				recipient : val,
				type : send_type,
				init: isInit? true : false
			},
			success:function(data,txtStatus){
				if (data) {
					if (data.error_code && 404 == parseInt(data.error_code)) {
						$("#send_info").addClass("error").text(MESSAGE.VALIDATE_DIALOG_VALIDATE_MOBILE_INVALID);
						setValidateButtonEnable(false);
						setSendButtonEnable(false);
						return;
					}
					var send_waiting_time = 0;
					if (data.send_waiting_time && parseInt(data.send_waiting_time)>0) {
						send_waiting_time = parseInt(data.send_waiting_time);
					}
					setSendStatus(data.send_remain_count,send_waiting_time);
					$("#time_info").countdown({
						init:send_waiting_time,
						afterFinish: function() {
							setSendStatus(data.send_remain_count,0);
						},
						timeIn: function(send_waiting_time) {
							if (send_waiting_time) {
								setSendStatus(data.send_remain_count,send_waiting_time);
							}
						}
					});
					setValidateButtonLocked(data.validate_locked);
					if (!data.has_code) {
						setValidateButtonEnable(false);
					}
				}
			},
			error:function(data,txtStatus){
				$("#send_info").addClass("error").text(MESSAGE.VALIDATE_DIALOG_SEND_SERVER_ERROR);
//				alert(MESSAGE.VALIDATE_DIALOG_SEND_SERVER_ERROR);
				setValidateButtonEnable(false);
				setSendButtonEnable(true);
			}
		});
	}

	function setSendStatus(send_remain_count, send_waiting_time) {
		if (send_waiting_time > 0) {
			$("#send_code_btn").removeClass("button_long").addClass("button_long_disabled").attr("disabled","disabled");
		} else {
			$("#time_info").text("");
			if (!send_remain_count) {
				var error = MESSAGE.VALIDATE_DIALOG_SEND_INFO_EXCEEDED1 + Validate_Config['received_text'] + MESSAGE.VALIDATE_DIALOG_SEND_INFO_EXCEEDED2;
				if (!noSkip) {
					error += MESSAGE.VALIDATE_DIALOG_SEND_INFO_EXCEEDED3+ Validate_Config['received_text'] + MESSAGE.VALIDATE_DIALOG_SEND_INFO_EXCEEDED4;
					$("#skip_btn").show();
				}
				$("#send_info").addClass("error").text(error);
				setSendButtonEnable(false);
				adjustButtonArea($('#validationDialog'));
				return;
			} else {
				setSendButtonEnable(true);
			}
		}

		adjustButtonArea($('#validationDialog'));
	}

	function setSendButtonEnable(enable) {
		if (enable) {
			$("#send_code_btn").removeClass("button_long_disabled").addClass("button_long").removeAttr("disabled");
		} else {
			$("#send_code_btn").removeClass("button_long").addClass("button_long_disabled").attr("disabled","disabled");	
		}
	}

	function setValidateButtonLocked(validate_locked) {
		var error_msg = "";
		setValidateButtonEnable(!validate_locked);
		if (validate_locked) {
			var error_msg = MESSAGE.VALIDATE_DIALOG_VALIDATE_INFO_LOCK1;
			if (Constant.VALIDATE_LOCK_TIME > 1) {
				error_msg += Constant.VALIDATE_LOCK_TIME + MESSAGE.VALIDATE_DIALOG_VALIDATE_INFO_LOCK2;
			} else {
				error_msg += Constant.VALIDATE_LOCK_TIME + MESSAGE.VALIDATE_DIALOG_VALIDATE_INFO_LOCK3;
			}
			error_msg += MESSAGE.VALIDATE_DIALOG_VALIDATE_INFO_LOCK4;
			$("#validate_info").text(error_msg).show();
		} else {
			$("#validate_info").text("").show();
		}
	}

	function setValidateButtonEnable(enable) {
		if (enable) {
			$("#validate_code_btn").addClass("positive_button").removeClass("positive_button_disabled").removeAttr("disabled");
			$("#validate_code_input").removeAttr("disabled");
		} else {
			$("#validate_code_btn").addClass("positive_button_disabled").removeClass("positive_button").attr("disabled", "disabled");
			$("#validate_code_input").attr("disabled", "disabled");
		}
	}

	function removeValidateTimer() {
		var jObj = $("#time_info");
		clearInterval(jObj.data("validate_timer"));
		jObj.removeData("validate_timer");
	}
}

function adjustButtonArea(jDialogObj) {
	var buttonArea = $(".buttons", jDialogObj);
	var totalLength = jDialogObj.width();
	var buttonAreaLength = 0;
	buttonArea.children(":visible").each(function(){
		var jobj = $(this);
		buttonAreaLength += jobj.width();
		if (jobj.css("padding-left")) {
			buttonAreaLength += parseInt(jobj.css("padding-left"));
		}
		if (jobj.css("padding-right")) {
			buttonAreaLength += parseInt(jobj.css("padding-right"));
		}
		if (jobj.css("margin-left")) {
			buttonAreaLength += parseInt(jobj.css("margin-left"));
		}
		if (jobj.css("margin-right")) {
			buttonAreaLength += parseInt(jobj.css("margin-right"));
		}
	});
	buttonArea.css("padding-left",(totalLength-buttonAreaLength)/2+"px");
}

function setValidateStatus(type, makeDisabledIfVerified) {
	var Validate_Config = Validate_Configs[type];
	var confirmed_field = Validate_Config['confirmed_field'];
	var confirmed = BoolUtils.str2bool($("#id_"+confirmed_field).val());
	var jObj = $("#id_"+type);
	var jObjp = jObj.parent();
	jObjp.find('.verified').remove();
	if (confirmed) {
		if (makeDisabledIfVerified) {
			jObj.attr("readonly", "readonly").addClass("readonly_mock_disabled");
		}
		jObjp.find('.helptext').remove();
		jObjp.append('<span class="verified">'+MESSAGE.VALIDATE_VERIFIED+'</span>');
	} else {
		if (makeDisabledIfVerified) {
			jObj.removeAttr("readonly").removeClass("readonly_mock_disabled");
		}
	}
}