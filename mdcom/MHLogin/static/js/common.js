/**
 * interceptString
 *  Intercept string, if the string exceed the length, show "...".
 * @param {} srcStr
 * @param {} length
 * @return {}
 */
function interceptString(srcStr, length) {
	if (srcStr&&srcStr.length>length) {
		return srcStr.substring(0,length)+"...";
	} else {
		return srcStr;
	}
}

/* iPad platform verification */
window.isIPad = function(){
	var regexiPad = new RegExp(/iPad/);
	if(regexiPad.exec(navigator.userAgent) ) {
		return true;
	}
	return false;
};

/* DateUtils */
var DateUtils = {
	configs: {
		"en-us": {
			//"format": "MM/dd/yyyy",
			"reg":/^(\d{1,2})(\/)(\d{1,2})(\/)(\d{4})$/,
			"ypos": 5,
			"mpos": 1,
			"dpos": 3
		},
		"de": {
			//"format": "yyyy-MM-dd",
			"reg":/^(\d{4})(-)(\d{1,2})(-)(\d{1,2})$/,
			"ypos": 1,
			"mpos": 3,
			"dpos": 5
		}
	},
	isDate: function(val) {
		var d = this.getDate(val);
		if (!d) {
			return false;
		}
		return true;
	},
	isValidUnixDate: function(val) {
		var d = this.getDate(val);
		if (!d) {
			return false;
		}
		if (d.getFullYear()<1970) {
			return false;
		}
		return true;
	},
	getDate: function(val) {
		var config = this.configs[Constant.TIME_ZONE];
		var reg = config.reg;
		var ypos = config.ypos;
		var mpos = config.mpos;
		var dpos = config.dpos;
		var r = val.match(reg);
		if(!r) {
			return null;
		}
		var d = new Date(r[ypos], r[mpos]-1, r[dpos]);
		if(!(d.getFullYear()==r[ypos]&&(d.getMonth()+1)==r[mpos]&&d.getDate()==r[dpos])) {
			return null;
		}
		return d;
	},
	/**
	 * Convert number of seconds into time obj str
	 *
	 * @param integer secs Number of seconds to convert
	 * @return str
	 */
	secondsToTime: function(secs){
		var hours = Math.floor(secs / (60 * 60));

		var divisor_for_minutes = secs % (60 * 60);
		var minutes = Math.floor(divisor_for_minutes / 60);

		var divisor_for_seconds = divisor_for_minutes % 60;
		var seconds = Math.ceil(divisor_for_seconds);

		return {
			"h": hours,
			"m": minutes,
			"s": seconds
		};
	},
	secondsToTimeStr: function(secs){
		var timeOjb = this.secondsToTime(secs);
		var ret = '';
		if (timeOjb.h) {
			ret += StrUtils.int2str_fixedlength(timeOjb.h, 2, '0') + ":"
		}
		return ret + StrUtils.int2str_fixedlength(timeOjb.m, 2, '0') +":"
				+ StrUtils.int2str_fixedlength(timeOjb.s, 2, '0');
	}
};

window.initButtonStatus=function(){
	$('#inviteDialog .buttons').removeClass('longButtons longButtons2');
	$('#inviteDialog .buttons .button').removeClass('buttonR step1Next hidden buttonBackTo buttonCancel sendMail buttonCenter inviteNewProviderBack cancelSendStaffMail sendNewProviderEmail findProviderContent buttonBGray buttonLong');
	$('#inviteDialog .buttons .button').unbind('click');
	$('#inviteDialog').unbind('keypress');
};

//show dialog
window.showDialog=function(title, width, height, top,openFunc, closeFunc){
	var left = ($(document).width()-500) / 2;
	if(top==1){
		var top = $(window).height() * 0.20;
	}else if(top==0){
		var top = $(window).height() * 0.30;
	}else{
		var top = 0;
	}
	if(height==''){
		height='auto';
	}
	$('#inviteDialog').dialog( "destroy" );
	$('#inviteDialog').dialog({
		title:title,
		width:width,
		height:height,
		draggable:false,
		resizable:false,
		modal:true,
		position:[left, top],
		open:function(){
			$('#inviteDialog .buttons').show();
			initButtonStatus();
			if(typeof openFunc === 'function'){
				openFunc();
			}
		},
		close:function(){
			if(typeof closeFunc === 'function'){
				closeFunc();
			}
		}
	});
};

(function($) {
	$.fn.showDialog = function(title, width, height, top,openFunc, closeFunc){
		var $this = $(this);
		var left = 0
		var top = 0

		var wx =  $(document).width()-width
		if (wx > 0){
			left = wx / 2;
		}

		if(top==1){
			var top = $(window).height() * 0.20;
		}else if(top==0){
			var top = $(window).height() * 0.30;
		}

		if(height==''){
			height='auto';
		}
		$this.dialog( "destroy" );

		$this.dialog({
			title:title,
			width:width,
			height:height,
			draggable:false,
			resizable:false,
			modal:true,
			position:[left, top],
			open:function(){
				$this.find('.buttons').show();
				$this.find('.buttons .button').unbind('click');
				$this.unbind('keypress');
				if(typeof openFunc === 'function'){
					openFunc();
				}
			},
			close:function(){
				if(typeof closeFunc === 'function'){
					closeFunc();
				}
			}
		});
	}
})(jQuery);

//add by xlin in 20120417 to add global method for check object is null
window.isEmptyObject = function(obj){
	for(var name in obj){
		return false;
	}
	return true;
};

//add by xlin in 20120605
window.getPersonalName = function(val){
	var p = {};
	p['firstName']='';
	p['lastName']='';
	var r = /\w+/ig;
	if(val.indexOf(',')!=-1){//split string using first whitespace
		val=val.replace(',',' ');
	}
	val = val.replace(/\s{2,}/g," ");
	if(val.indexOf(' ')!=-1){
		p['firstName']=r.exec(val)[0];
		p['lastName']=$.trim(val.replace(p['firstName'],' '));
	}else{
		p['firstName'] = $.trim(val);
		p['lastName'] = '';
	}
	if(val == 'Email or name here'){
		p['firstName'] = '';
		p['lastName'] = '';
	}
	return p;
};

var BoolUtils = {
	str2bool: function(str) {
		if (!str) {
			return false;
		}
		
		if ("false" == str || "False" == str) {
			return false;
		}
		return true;
	}
};

String.prototype.replaceAll = function(s1,s2){
	return this.replace(new RegExp(s1,"gm"),s2);
};

var StrUtils = {
	int2str_fixedlength: function(val, length, ch) {
		if (!ch) {
			ch = '';
		}
		var ret = '';
		for (var i = 0; i < length; i++) {
			ret += ch;
		}
		ret += val;
		return ret.substr(ret.length-length,length);
	},
	bool2python_str: function(boolVal) {
		if (boolVal) {
			return 'True';
		} else {
			return 'False';
		}
	},
	parsePhoneNumber: function(num) {
		if (!num) {
			return "";
		}
		return num.replaceAll("\\(","").replaceAll("\\) ","").replaceAll("-","");
	},
	isPhone: function(val) {
		if(!Constant.CALL_ENABLE){
			return true;
		}
		return /^((\d{10})|(\(\d{3}\) |(\d{3}-)){1}(\d{3}-\d{4}))?$/.test(val);
	},
	isZipCode: function(val) {
		return /^\d{5,5}-\d{4,4}$/.test(val) || /^\d{5,5}$/.test(val);
	},
	//add by xlin in 20120425 to validate user name
	isUserName: function(val){
		return /^[a-zA-Z0-9_@+.-]{1,30}$/.test(val);
	},
	limitString: function(val, num, suffix){
		len = val.length;
		if(len <= num+suffix.length) {
			return val
		} else {
			str = '';
			str += '<span title="'+ val +'">';
			str += val.substring(0,num) + suffix;
			str += '</span>'
			return str;
		}
	},
	//add by xlin 20120716 to validate get doctorcom number
	isPinCode:function(val){
		return /\b\d{4,8}\b/.test(val);
	},
	isAreaCode:function(val){
		return /[2-9][0-8][0-9]/.test(val);
	},
	//add by xlin 121017 to check first name text equal 'first name'
	isFirstNameText:function(val){
		return !/First Name/.test(val);
	},
	//add by xlin 121017 to check last name text equal 'last name'
	isLastNameText:function(val){
		return !/Last Name/.test(val);
	},
	//add by xlin 130117 to check date is after today
	isAfterToday:function(val){
		var t = new Date(val);
		var today = new Date();
		if((t-today)>0){
			return false;
		}else{
			return true;
		}
	}
};

var ORT_ROLE_TYPE=['Member','Organization Admin','Super Organization Admin'];
Array.prototype.remove=function(dx){
	if(isNaN(dx)||dx>this.length){return false;}
	for(var i=0,n=0;i<this.length;i++){
		if(this[i]!=this[dx]){
			this[n++]=this[i];
		}
	}
	this.length-=1
}


/*** it is sprintf.js below, it makes string format is easy. 
	https://github.com/alexei/sprintf.js
 ***/
/*! sprintf.js | Copyright (c) 2007-2013 Alexandru Marasteanu <hello at alexei dot ro> | 3 clause BSD license */
var sprintf = function() {
	if (!sprintf.cache.hasOwnProperty(arguments[0])) {
		sprintf.cache[arguments[0]] = sprintf.parse(arguments[0]);
	}
	return sprintf.format.call(null, sprintf.cache[arguments[0]], arguments);
};

sprintf.format = function(parse_tree, argv) {
	var cursor = 1, tree_length = parse_tree.length, node_type = '', arg, output = [], i, k, match, pad, pad_character, pad_length;
	for (i = 0; i < tree_length; i++) {
		node_type = get_type(parse_tree[i]);
		if (node_type === 'string') {
			output.push(parse_tree[i]);
		}
		else if (node_type === 'array') {
			match = parse_tree[i]; // convenience purposes only
			if (match[2]) { // keyword argument
				arg = argv[cursor];
				for (k = 0; k < match[2].length; k++) {
					if (!arg.hasOwnProperty(match[2][k])) {
						throw(sprintf('[sprintf] property "%s" does not exist', match[2][k]));
					}
					arg = arg[match[2][k]];
				}
			}
			else if (match[1]) { // positional argument (explicit)
				arg = argv[match[1]];
			}
			else { // positional argument (implicit)
				arg = argv[cursor++];
			}

			if (/[^s]/.test(match[8]) && (get_type(arg) != 'number')) {
				throw(sprintf('[sprintf] expecting number but found %s', get_type(arg)));
			}
			switch (match[8]) {
				case 'b': arg = arg.toString(2); break;
				case 'c': arg = String.fromCharCode(arg); break;
				case 'd': arg = parseInt(arg, 10); break;
				case 'e': arg = match[7] ? arg.toExponential(match[7]) : arg.toExponential(); break;
				case 'f': arg = match[7] ? parseFloat(arg).toFixed(match[7]) : parseFloat(arg); break;
				case 'o': arg = arg.toString(8); break;
				case 's': arg = ((arg = String(arg)) && match[7] ? arg.substring(0, match[7]) : arg); break;
				case 'u': arg = arg >>> 0; break;
				case 'x': arg = arg.toString(16); break;
				case 'X': arg = arg.toString(16).toUpperCase(); break;
			}
			arg = (/[def]/.test(match[8]) && match[3] && arg >= 0 ? '+'+ arg : arg);
			pad_character = match[4] ? match[4] == '0' ? '0' : match[4].charAt(1) : ' ';
			pad_length = match[6] - String(arg).length;
			pad = match[6] ? str_repeat(pad_character, pad_length) : '';
			output.push(match[5] ? arg + pad : pad + arg);
		}
	}
	return output.join('');
};

sprintf.cache = {};

sprintf.parse = function(fmt) {
	var _fmt = fmt, match = [], parse_tree = [], arg_names = 0;
	while (_fmt) {
		if ((match = /^[^\x25]+/.exec(_fmt)) !== null) {
			parse_tree.push(match[0]);
		}
		else if ((match = /^\x25{2}/.exec(_fmt)) !== null) {
			parse_tree.push('%');
		}
		else if ((match = /^\x25(?:([1-9]\d*)\$|\(([^\)]+)\))?(\+)?(0|'[^$])?(-)?(\d+)?(?:\.(\d+))?([b-fosuxX])/.exec(_fmt)) !== null) {
			if (match[2]) {
				arg_names |= 1;
				var field_list = [], replacement_field = match[2], field_match = [];
				if ((field_match = /^([a-z_][a-z_\d]*)/i.exec(replacement_field)) !== null) {
					field_list.push(field_match[1]);
					while ((replacement_field = replacement_field.substring(field_match[0].length)) !== '') {
						if ((field_match = /^\.([a-z_][a-z_\d]*)/i.exec(replacement_field)) !== null) {
							field_list.push(field_match[1]);
						}
						else if ((field_match = /^\[(\d+)\]/.exec(replacement_field)) !== null) {
							field_list.push(field_match[1]);
						}
						else {
							throw('[sprintf] huh?');
						}
					}
				}
				else {
					throw('[sprintf] huh?');
				}
				match[2] = field_list;
			}
			else {
				arg_names |= 2;
			}
			if (arg_names === 3) {
				throw('[sprintf] mixing positional and named placeholders is not (yet) supported');
			}
			parse_tree.push(match);
		}
		else {
			throw('[sprintf] huh?');
		}
		_fmt = _fmt.substring(match[0].length);
	}
	return parse_tree;
};

var vsprintf = function(fmt, argv, _argv) {
	_argv = argv.slice(0);
	_argv.splice(0, 0, fmt);
	return sprintf.apply(null, _argv);
};

/**
 * helpers
 */
function get_type(variable) {
	return Object.prototype.toString.call(variable).slice(8, -1).toLowerCase();
}

function str_repeat(input, multiplier) {
	for (var output = []; multiplier > 0; output[--multiplier] = input) {/* do nothing */}
	return output.join('');
}

/*** it is sprintf.js above, it makes string format is easy. ***/
String.prototype.sprintf = function(){
	var argus = [];
	argus.push(this);
	for(var i=0;i <arguments.length;i++) {
		argus.push(arguments[i]);
	}
	return sprintf.apply(null, argus);
};
String.prototype.vsprintf = function(){
	var argus = [];
	argus.push(this);
	for(var i=0;i <arguments.length;i++) {
		argus.push(arguments[i]);
	}
	return vsprintf.apply(null, argus);
};


(function($) {
	//type: 0-provider, 1-staff
	//isAjax: true/false
	//ajaxFun: if isAjax, this is ajax success function
	$.fn.CreateUser = function(type, isAjax, ajaxFun){
		$(this).unbind('click');
		return this.click(function(){
			if (type == 0){
				if (isAjax){
					$.comAjax({
						url: "/Organization/Member/ProviderCreate/",
						type:'GET',
						data: {},
						success:function(data, status){
							ajaxFun(data);
						}
					});
				} else {
					location.href='/Practice/Staff/newProvider/';
				}
				
			} else if (type == 1){
				if (isAjax){
					$.comAjax({
						url: "/Organization/Member/StaffCreate/",
						type:'GET',
						data: {},
						success:function(data, status){
							ajaxFun(data);
						}
					});
				} else {
					location.href='/Practice/Staff/newStaff/';
				}
			}
		});
	}
})(jQuery);