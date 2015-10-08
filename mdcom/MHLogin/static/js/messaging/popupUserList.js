(function($) {
	$.fn.AddRecipientUser = function(){
		var $this = $(this);
		var sWidth = 800
		var left = ($(document).width()-sWidth) / 2;
		var top = $(window).height() * 0.20;
		$('#recPopUsrDiv').html($this.html());
		$("#RicipientDialog").comDialog({
			title:MESSAGE.POPUP_USER_LIST_TITLE,
			width:sWidth,
			draggable:false,
			resizable:false,
			modal:true,
			position:[left, top],
			open:function(){
				RefreshUser(true);
			},
			has_btn_divide_line: false,
			dc_buttons: {
				"OK": {
					'click': function() {
						var content = $('#recPopUsrDiv').html();
						$this.html(content);
						$(this).dialog("close");
					},
					'text': MESSAGE.POPUP_USER_LIST_OK,
					'class': 'positive-btn'
				},
				"No": {
					'click': function() {
						$(this).dialog("close");
					},
					'text': MESSAGE.POPUP_USER_LIST_CANCEL
				}
			}
		});
	}
})(jQuery);

function removeRicUsr(self) {
	$(self).parent().remove();
}

function RefreshUser(isClean) {
	if(isClean){
		$("#userPopConTab input:radio").filter('[value="all"]').attr('checked', true);
		$("#userNameFilter").val('')
		$("#userNameFilter").Watermark(MESSAGE.POPUP_USER_LIST_SEARCH_BY_NAME);
	}
	var type = $("#userPopConTab input:radio[name='userTypeGroup']:checked").val();
	var name = $("#userNameFilter").val();
	if(name == MESSAGE.POPUP_USER_LIST_SEARCH_BY_NAME){
		name = '';
	}
	
	var tbody = '<tr><td colspan="4" align="center"><img alt="loading"'
	tbody += 'src="/static/img/loadinfo_d3.gif" style="margin:120px 0;" /></td></tr>';
	$('#userTable tbody').html(tbody);
	$('#userNameFilterbtn').attr("disabled","disabled"); 
	$('#userTable tbody tr').unbind('dblclick');
	$('#userTable tbody tr').unbind('click');
	
	$.ajax({
		url: '/Search/User/AJAX/GetProviders/',
		data:{'type':type, 'name':name},
		type:'POST',
		dataType: 'json',
		success:function(data){
			tbody = '';
			$.each(data, function(i,user){
				if(i%2==1){
					tbody += '<tr class="odd">';
				} else {
					tbody += '<tr class="even">';
				}
				tbody += '<td class="tr_id" style="display:none;">'+user.id+'</td>';
				tbody += '<td class="tr_name" style="width:120px">'+user.fullname+'</td>';
				tbody += '<td style="width:100px">'+user.user_type+'</td>';
				tbody += '<td>'+user.office_address+'</td>';
				tbody += '<td style="width:160px">'+user.specialty+'</td>';
				tbody += '</tr>';
			});
			
			$('#userTable tbody').html(tbody);
			$('#userNameFilterbtn').attr("disabled",""); 
			
			$('#userTable tbody tr').bind('click', function(event) {
				$(this).removeClass('selected');
				var tr_id = $(this).find('.tr_id').html();
				var tr_name = $(this).find('.tr_name').html();
				var content = getUsrSpan(tr_id,tr_name);

				if($('#recPopUsrDiv').html().indexOf('>'+tr_id+'<') == -1){
					$('#recPopUsrDiv').append(content);
				}
			});
		},
		error: function(jqXHR,textStatus, errorThrown) {
			alert('{% trans "An error occurred. Please try again...." %}');
		}
	});	
}

function getUsrSpan(id,name) {
	var html = ""
	html += '<span class="root_span" style="margin-left:5px;">';
	html += '<span class="id_span" style="display:none;">';
	html += id;
	html += '</span>';
	html += name;
	html += '<a style="cursor: pointer;" onclick="removeRicUsr(this);">'
	html += '<img alt="Del" src="/static/img/icon_close2.png" /></a>';
	html += ';';
	html += '</span>';
	return html;
}

function getUsrSpanVal() {
	var val = ''
	$("#recipToDiv span.root_span").each(function(){
		val += $(this).find('.id_span').html();
		val += ',';
	});
	$('#id_user_recipients').val(val);
	
	var val_cc = ''
	$("#recipCcDiv span.root_span").each(function(){
		val_cc += $(this).find('.id_span').html();
		val_cc += ',';
	});
	$('#id_user_cc_recipients').val(val_cc);
}

function getUsrReferSpanVal() {
	var val = ''
	$("#recipToDiv span.root_span").each(function(){
		val += $(this).find('.id_span').html();
		val += ',';
	});
	$('#id_user_to_recipients').val(val);
	
	var val_cc = ''
	$("#recipCcDiv span.root_span").each(function(){
		val_cc += $(this).find('.id_span').html();
		val_cc += ',';
	});
	$('#id_user_cc_recipients').val(val_cc);
}
