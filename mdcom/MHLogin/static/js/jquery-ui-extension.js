jQuery.extend({
	comAjax : function(args) {
		var waitId = null;
		var defaultOpts = {
			"reload_if_error": false,
			"stay_loading_while_complete": false,
			"error_timeout": MESSAGE.JQUERY_UI_COMAJAX_TIMEOUT,
			"error_601": MESSAGE.JQUERY_UI_COMAJAX_ERROR_601,
			"error_404": MESSAGE.JQUERY_UI_COMAJAX_ERROR_404,
			"error_500": MESSAGE.JQUERY_UI_COMAJAX_SERVER_ERROR
		}
		var opts = $.extend(defaultOpts, args);
		var defaultAjaxOpts = {
			type : "GET",
			cache : false,
			timeout:30000,
			error : function(XMLHttpRequest, error, errorThrown) {
				if(error==="timeout") {
					alert(opts["error_timeout"]);
					return;
				}
				if (XMLHttpRequest.status == 601) {
					alert(opts["error_601"]);
				} else if (XMLHttpRequest.status == 404) {
					alert(opts["error_404"]);
				} else if (XMLHttpRequest.status == 400) {
					if (!XMLHttpRequest.response) {
						return;
					}
					var result = XMLHttpRequest.response;
					if (typeof(result)!="object") {
						result = JSON.parse(XMLHttpRequest.response);
					}
					var errs = '';
					if (result.errors) {
						if (typeof(result.errors) == "object") {
							for (error in result.errors) {
								errs += error + ": " + result.errors[error] + "\n";
							}
						} else {
							errs = result.errors;
						}
					} else {
						errs = result;
					}
					alert(errs);
				} else if (XMLHttpRequest.status == 500) {
					alert(opts["error_500"]);
				} else {
					if (XMLHttpRequest.responseText) {
						alert(XMLHttpRequest.responseText);
					} else {
						alert(opts["error_500"]);
					}
				}
				if (opts["reload_if_error"]) {
					window.location.href = window.location.href;
				}
			},
			beforeSend : function() {
				waitId = $.ui.wait.start(MESSAGE.JQUERY_UI_COMAJAX_MSG_LOAD);
			},
			complete : function() {
				if (!opts["stay_loading_while_complete"]) {
					$.ui.wait.stop(waitId);
				}
			}
		};

		args = $.extend(defaultAjaxOpts, args);
		return jQuery.ajax(args);
	}
});

$.extend($.ui, {
	wait: function() {
		this.$el = $.ui.wait.start();
	}
});

$.extend($.ui.wait, {
	instances: {},
	maxId: 0,
	$el: null,
	$el_wait: null,
	timer:0,
	start: function(msg) {
		if (!$.ui.wait.$el) {
			$.ui.wait.$el = $('<div id="loading_overlay" style="z-index:99999;"></div>')
//				.addClass('ui-widget-overlay')
				.appendTo(document.body)
				.css({
					left: "0px",
					top: "0px",
					position: "absolute",
					width: $.ui.wait.width(),
					height: $.ui.wait.height()
				});
			if (!msg) {
				msg = "";
			}	
			
			$.ui.wait.$el_wait = $('<div style="z-index:100000;border:1px solid #B5B5B5;background:#EEEEEE;">'
					+'<div style="padding:5px 0 0 85px;">'
					+'<div class="waiting-white" style="float: left;"><img src="/static/img/waiting.gif"></div>'
					+'<div class="waiting-msg" style="float: left;font-weight:bold;font-size:12px;color:#111111;">&nbsp;&nbsp;'+ msg + '</div>'
					+'</div>'
					+'</div>')
				.appendTo($.ui.wait.$el)
				.css({
					position: "absolute",
					top: $.ui.wait.top_wait(),
					left: $.ui.wait.left_wait(),
					"margin-top": "-15px",
					"margin-left": "-125px",
					width: "250px",
					height: "30px",
					opacity: "0.8",
					filter: "alpha(opacity=80)"
				});
			$(window).bind('resize', $.ui.wait.resize);
			setTimeout(function(){
				$.ui.wait.timer = 1;
			}, 500);
//		var $el_wait_idivs = $el_wait.children();
//		var $el_wait_width = $el_wait_idivs.eq(0).width() + $el_wait_idivs.eq(1).width() + 6;
//		var $el_wait_height = 30;
//		$el_wait.appendTo($.ui.wait.$el)
//			.css({
//				position: "absolute",
//				top: $.ui.wait.top_wait(),
//				left: $.ui.wait.left_wait(),
//				"margin-top": "-"+$el_wait_height/2+"px",
//				"margin-left": "-"+$el_wait_width+"px",
//				width: $el_wait_width+"px",
//				height: $el_wait_height+"px",
//				opacity: "0.7",
//				filter: "alpha(opacity=70)"
//			});				
		}
		var id = $.ui.wait.maxId++;
		$.ui.wait.instances[id] = true;
		return id;
	},

	stop: function(id) {
		if ($.ui.wait.timer == 1) {
			$.ui.wait.destroy(id);
		} else {
			setTimeout(function(){
				$.ui.wait.destroy(id);
			}, 500);
		}
	},

	destroy: function(id) {
		if ($.ui.wait.instances[id]) {
			delete $.ui.wait.instances[id];
		}

		var count = 0;
		for (attr in $.ui.wait.instances) {
			count++;
		}

		if (count == 0 && $.ui.wait.$el) {
			$.ui.wait.$el.remove();
			$.ui.wait.$el = null;
			$.ui.wait.$el_wait = null;
			$.ui.wait.timer = 0;
		}
	},

	height: function() {
		var scrollHeight,
			offsetHeight;
		// handle IE 6
		if ($.browser.msie && $.browser.version < 7) {
			scrollHeight = Math.max(
				document.documentElement.scrollHeight,
				document.body.scrollHeight
			);
			offsetHeight = Math.max(
				document.documentElement.offsetHeight,
				document.body.offsetHeight
			);

			if (scrollHeight < offsetHeight) {
				return $(window).height() + 'px';
			} else {
				return scrollHeight + 'px';
			}
		// handle "good" browsers
		} else {
			return $(document).height() + 'px';
		}
	},

	width: function() {
		var scrollWidth,
			offsetWidth;
		// handle IE
		if ( $.browser.msie ) {
			scrollWidth = Math.max(
				document.documentElement.scrollWidth,
				document.body.scrollWidth
			);
			offsetWidth = Math.max(
				document.documentElement.offsetWidth,
				document.body.offsetWidth
			);

			if (scrollWidth < offsetWidth) {
				return $(window).width() + 'px';
			} else {
				return scrollWidth + 'px';
			}
		// handle "good" browsers
		} else {
			return $(document).width() + 'px';
		}
	},

	top_wait: function() {
		var top = $(window).height()*0.381+$(window).scrollTop();
		return top + "px";
	},
	
	left_wait: function() {
		var left = $(window).width()/2+$(window).scrollLeft();
		return left + "px";
	},
	
	resize: function() {
		if ($.ui.wait.$el) {
			$.ui.wait.$el.css({
				width: 0,
				height: 0
			}).css({
				width: $.ui.wait.width(),
				height: $.ui.wait.height()
			});
			$.ui.wait.$el_wait.css({
				top: $.ui.wait.top_wait(),
				left: $.ui.wait.left_wait()
			});
		}
	}
});

/*
 * jWait
 * 	Show a waiting dialog.
 * 	You can configure the below parameter to cover the default values.
 * 		{	
 * 			width:			The width of dialog, default: 500,
 * 			height:130,		The height of dialog, default: 130,
 * 			title: 			The title of dialog, default: "Waiting",
 * 			msg: 			The displayed message of dialog, default: "Waiting",
 * 			cancelEnable: 	Whether show the cancel button, default: "true",
 * 			cancelFunc: 	The event of the cancel button, default: "false", do nothing,
 * 			zIndex: 		The z-index value of the dialog, default: "1000",
 * 			resizable: 		Whether can resize the dialog, default: "false",
 * 			draggable: 		Whether can drag the dialog, default: "true"
 * 		}
 * Depends:
 *	jquery-ui-1.8.2
 */
function jWait(options) {
	var opt = $.extend({
			width:500,
			height:160,			
			title: MESSAGE.JQUERY_UI_JWAIT_TITLE,
			msg: MESSAGE.JQUERY_UI_JWAIT_MSG,
			cancelEnable: true,
			cancelFunc: null,
			zIndex: 1000,
			resizable: false,
			draggable: true
		},options);

	var dialogWait = $("#dialogWait");
	if (dialogWait.size()<1) {
		$("body").append('<div id="dialogWait"></div>');
		dialogWait = $("#dialogWait");
		var conf = {
			autoOpen:false,
			title:opt.title,
			modal: true,
			resizable: opt.resizable,
			draggable: opt.draggable,
			width:opt.width,
			height:opt.height,
			closeOnEscape: false,
			zIndex: opt.zIndex,
			open: function(event, ui) { 
				var dialogContainer = $('#dialogWait').parent();
				dialogContainer.find('a.ui-dialog-titlebar-close').hide();
				dialogContainer.find('.ui-dialog-buttonpane').width(opt.width-40)
					.find('.ui-dialog-buttonset').width(106)
					.find('button').trigger("blur");
				
				//dialogContainer.find('button').removeClass("ui-corner-all").removeClass("ui-state-default").css({"color":'#003399','font-weight':'bold'}).hover(function(){$(this).removeClass("ui-state-hover");});
			},
			close: function(event, ui) {
				if (opt.cancelFunc) {
					opt.cancelFunc();
				}	
				$(this).remove();
			} 					
		};
		
		if (opt.cancelEnable) {
			conf.buttons = {
				"Cancel": function() {
					if (opt.cancelFunc) {
						opt.cancelFunc();
					}	
					$(this).remove();
				}
			};
		}
		dialogWait.dialog(conf);
	}
	var html='<div style="padding:10px;float:left;"><img src="/static/img/waiting.gif"/><span id="wait_msg" style="padding:0 0 0 20px;">'+opt.message+'</span></div>';					
	//var html='<div style="padding:10px;">'
	//		+'<img src="/static/img/icons/wait-left.gif"/>'
	//		+'<span id="wait_msg" style="0 10px;">'+opt.message+'</span>'
	//		+'<img src="/static/img/icons/wait-right.gif"/>'
	//		+'</div>';			
	dialogWait.html(html);
	dialogWait.dialog('open');
	return dialogWait;
} 


/*
 * 
 */ 
(function($) {
	$.fn.countdown = function(options) {
		var opt = $.extend({
			prev_str:"(",
			next_str:")",
			init: 120,							// unit: second
			frequency: 1000,					// unit: millisecond
			afterFinish: false,					// function, is excuted after finish countdown
			timeIn: false						// function, is excuted during countdown
		}, options);

		var validate_timer;
		return this.each(
			function(){
				var jObj=$(this);
				if (opt.init) {
					jObj.attr('remain_time', opt.init);
					setTime(opt.init);
					if (validate_timer) {
						clearInterval(validate_timer);
					}
					execute();
					validate_timer = setInterval(function(){
						execute();
					}, opt.frequency);
					jObj.data("validate_timer",validate_timer);
				}

				function execute(){
					var remain_time = parseInt(jObj.attr('remain_time'));
					if (remain_time > 0) {
						jObj.attr('remain_time', remain_time-1);
						setTime(remain_time);
						if (opt.timeIn) {
							opt.timeIn(remain_time);
						}
					} else {
						setTime(0);
						if (validate_timer) {
							clearInterval(validate_timer);
							if (opt.afterFinish) {
								opt.afterFinish();
							}
						}
					}
				}

				function timeIn(remain_time) {
					if (opt.timeIn) {
						opt.timeIn(remain_time);
					}
					setTime(remain_time);
				}

				function setTime(secs){
					jObj.text(opt.prev_str+DateUtils.secondsToTimeStr(secs)+opt.next_str);
				}
			}
		);
	};
})(jQuery);

(function($) {
	$.fn.comDialog = function(options) {
		var opts = $.extend({
				minHeight: 110,
				minWidth: 250,
				left: false,
				top: false,
				zIndex: 1000,
				draggable:false,
				resizable:false,
				modal:true,
				auto_focus: false,
				has_btn_divide_line: true,
				dc_buttons: false
		}, options);

		if (!opts.width) {
			opts.width = 550;
		}
		if (!opts.position) {
			if (opts.left && opts.top) {
				opts.position = [opts.left, opts.top];
			} else {
				if (opts.height && opts.width) {
					// golden section
					var top = ($(window).height()-opts.height)*0.381;
					var left = 0;
					var wx =  $(document).width()-opts.width;
					if (wx > 0){
						left = wx / 2;
					}
					opts.position = [left, top];
				}
			}
		}

		opts.open = function(event, ui) {
			if (options.open) {
				options.open(event, ui)
			}
			if (!opts.auto_focus) {
				$(this).find(':tabbable').blur()
			}
			if (opts.dc_buttons && opts.dc_buttons) {
				//$( this ).dialog( "_createButtons");
				_createDCButtons(this, opts.dc_buttons);
			}
		};

		var attrFn = $.attrFn || {
			val: true,
			css: true,
			html: true,
			text: true,
			data: true,
			width: true,
			height: true,
			offset: true,
			click: true
		};

		var _createDCButtons= function(obj, buttons) {
			var self = $(obj),
				hasButtons = false,
				uiDialogButtonPane = $('<div></div>')
					.addClass(
						'ui-dialog-dc-buttonpane ' +
						'ui-widget-content ' +
						'ui-helper-clearfix'
					),
				uiButtonSet = $( "<div></div>" )
					.addClass( "ui-dialog-buttonset" )
					.appendTo( uiDialogButtonPane );
			if (opts.has_btn_divide_line) {
				uiDialogButtonPane.addClass("ui-dialog-dc-buttonpane-border");
			}
			// if we already have a button pane, remove it
			self.parent().find('.ui-dialog-dc-buttonpane').remove();
	
			if (typeof buttons === 'object' && buttons !== null) {
				$.each(buttons, function() {
					return !(hasButtons = true);
				});
			}

			if (hasButtons) {
				$.each(buttons, function(name, props) {
					props = $.isFunction( props ) ?
						{ click: props, text: name } :
						props;
					if (!props.hidden) {
						var button = $('<div><div class="left slice"></div><div class="center slice"></div><div class="right slice"></div></div>');
						if (!props.disabled) {
							button.click(function() {
								props.click.apply(obj, arguments);
							});
						}
						button.appendTo(uiButtonSet);
						// can't use .attr( props, true ) with jQuery 1.3.2.
						$.each( props, function( key, value ) {
							if ( key === "click" ) {
								return;
							}
							if ( key === "text" ) {
								button.find(".center")[ key ]( value );
								return;
							}
							if ( key in attrFn ) {
								button[ key ]( value );
							} else {
								button.attr( key, value );
							}
						});
						if ($.fn.button) {
							button.button();
						}
						button.html(button.find('span').html());
					}
				});
				uiDialogButtonPane.appendTo(self.parent());
			}
		};

		var $this = $(this);
		var dialog = $this.dialog(opts);
		return dialog;
	};
})(jQuery);

function showSimpleDialog(options) {
	var opts = $.extend({
			content: '',
			width: 550,
			height: 110
		},options);
	opts.close = function(event, ui) {
		if (options.close) {
			options.close(event, ui)
		}
		$(this).remove();
	};

	$("#simpleDialog").remove();
	$("body").append('<div id="simpleDialog" class="main-content"></div>');
	var simpleDialog = $("#simpleDialog").comDialog(opts);
	simpleDialog.html(opts.content);
	simpleDialog.dialog('open');
	return simpleDialog;
} 
