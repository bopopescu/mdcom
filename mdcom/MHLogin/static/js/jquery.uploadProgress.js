/*
 * jquery.uploadProgress
 *
 * Copyright (c) 2008 Piotr Sarnacki (drogomir.com)
 *
 * Licensed under the MIT license:
 *   http://www.opensource.org/licenses/mit-license.php
 *
 */
(function($) {
  $.fn.uploadProgress = function(options) {
	options = $.extend({
		interval: 2000,
		progressBar: "#progressbar",
		progressUrl: "/progress",
		start: function() {},
		uploading: function() {},
		complete: function() {},
		success: function() {},
		error: function() {},
		netAbort: function() {},
		preloadImages: [],
		uploadProgressPath: '/javascripts/jquery.uploadProgress.js',
		jqueryPath: '/javascripts/jquery.js',
                              timer: ""
	}, options);
	
	$(function() {
		//preload images
		for(var i = 0; i<options.preloadImages.length; i++)
		{
		  options.preloadImages[i] = $("<img>").attr("src", options.preloadImages[i]);
		}
		/* tried to add iframe after submit (to not always load it) but it won't work. 
		safari can't get scripts properly while submitting files */
//		if($.browser.safari && top.document == document) {
		if($.browser.safari) {
			/* iframe to send ajax requests in safari 
			   thanks to Michele Finotto for idea */
			iframe = document.createElement('iframe');
			iframe.name = "progressFrame";
			$(iframe).css({width: '0', height: '0', position: 'absolute', top: '-3000px'});
			document.body.appendChild(iframe);
			
			var d = iframe.contentWindow.document;
			d.open();
			/* weird - safari won't load scripts without this lines... */
			d.write('<html><head></head><body></body></html>');
			d.close();
			
			var b = d.body;
			var s = d.createElement('script');
			s.src = options.jqueryPath;
			/* must be sure that jquery is loaded */
			s.onload = function() {
				var s1 = d.createElement('script');
				s1.src = options.uploadProgressPath;
				b.appendChild(s1);
			}
			b.appendChild(s);
		}
	});
  
	return this.each(function(){
		$(this).bind('submit', function() {
			var uuid = "";
			for (i = 0; i < 32; i++) { uuid += Math.floor(Math.random() * 16).toString(16); }
			
                /* update uuid */
                options.uuid = uuid;
				/* start callback */
				options.start();

			/* patch the form-action tag to include the progress-id 
                           if X-Progress-ID has been already added just replace it */
            if(old_id = /X-Progress-ID=([^&]+)/.exec($(this).attr("action"))) {
              	var action = $(this).attr("action").replace(old_id[1], uuid);
              	$(this).attr("action", action);
            } else {
			  	//$(this).attr("action", jQuery(this).attr("action") + "?X-Progress-ID=" + uuid);
                var action = jQuery(this).attr("action"); 
                if (action.indexOf("?")>0) {
                	$(this).attr("action", action + "&X-Progress-ID=" + uuid);
                } else {
                	$(this).attr("action", action + "?X-Progress-ID=" + uuid);
                }
			}
			var uploadProgress = $.browser.safari ? progressFrame.jQuery.uploadProgress : jQuery.uploadProgress;
			options.timer = window.setInterval(function() { uploadProgress(this, options) }, options.interval);
		});
	});
  };

jQuery.uploadProgress = function(e, options) {
	jQuery.ajax({
		type: "GET",
		url: options.progressUrl,
		dataType: "json",
		data:{"X-Progress-ID":options.uuid},
		beforeSend: function(xhr) {
			xhr.setRequestHeader("X-Progress-ID", options.uuid);
		},
        cache:false,
		complete:function(XMLHttpRequest,textStatus) {
			if (XMLHttpRequest.readyState==4&&(XMLHttpRequest.status==0||XMLHttpRequest.status==12029)) {
				options.netAbort();
			}				
		},
        success: function(upload) {
        	if (upload) {
	            if (upload.state == 'uploading') {
	                if (upload.size>0) {
	                    upload.percents = Math.floor((upload.received / upload.size)*1000)/10;
	                    
	                    var bar = $.browser.safari ? $(options.progressBar, parent.document) : $(options.progressBar);
	                    bar.css({width: upload.percents+'%'});
	                    options.uploading(upload);              
	                }
	            }
	            
	            if (upload.state == 'done' || upload.state == 'error') {
	                window.clearTimeout(options.timer);
	                options.complete(upload);
	            }
	            
	            if (upload.state == 'done') {
	                options.success(upload);
	            }
	            
	            if (upload.state == 'error') {
	                options.error(upload);
	            }       	
        	}

        }
	});
};

})(jQuery);

/*
 * jquery.multiUploadProgress
 *	The plugin integrate DoctorCom's business logic and jquery.uploadProgress.js.
 *	If you want to use this plugin, you need to config the parameters only:
 *		after_upload: The name of method that executed after upload success.
 *			default: nothing.
 *		before_abort_upload: The name of method that executed before upload aborting.
 *			default: nothing.
 *		max_upload_size: Uploaded file's max size.
 *			default: false.
 */
(function($) {
	$.fn.multiUploadProgress = function(options) {
		var opt = $.extend({
			after_upload:"",
			before_abort_upload:"",
			max_upload_size:false,
			custom_button: false
		}, options);
		var id_file = $(this).attr("id");
		return this.each(function(){
			var jObj = $(this);
			jObj.data('opt',opt);
			var tempDivHtml = '<div class="file_readonly_area">';
			if (opt.custom_button) {
				tempDivHtml += '<span id="upload_btn" class="upload_btn" onclick="do_upload();"><img src="/static/img/upload_icon.png"/>Click to Upload</span>';
			} else {
				tempDivHtml += '<input type="file" size="25" name="file" id="id_file" disabled="disabled">';
			}

			if (opt.max_upload_size) {
				tempDivHtml += '<span id="id_max_size_msg"> ('+MESSAGE.UPLOAD_FILE_MAX_SIZE+opt.max_upload_size+' M.)</span>';
			}
			tempDivHtml += '</div>'
						+ '<div class="upload_container"></div>';
			$(tempDivHtml).prependTo(jObj);
			//$('<div class="upload_panel_container"></div>').appendTo(jObj);
			jObj.addClass("upload_outer_container");
			addUploadArea(jObj.attr("id"));
		});
  };
})(jQuery);

function addUploadArea(uploadAreaId) {
	var jObj = $("#"+uploadAreaId);
	var opt = jObj.data("opt");
	var url = '/Messages/Upload/?after_upload='+opt.after_upload+'&before_abort_upload='+opt.before_abort_upload+'&custom_button='+opt.custom_button;
	$('<div class="upload_panel" style="display:none;">'
		+'<iframe src="'+url
		+'" height="25" width="600" scrolling="no" frameborder="0">'
		+'</iframe>'
		+'</div>').prependTo(jObj.find(".upload_container"));
}
function deleteAttachment(obj) {
	if (confirm(MESSAGE.UPlOAD_DELETE_CONFIRM)) {
		var jObj = $(obj);
		var jPObj = jObj.parent().parent();
		var fileName = jPObj.find('input[name="file_saved_name"]').val();
		
		jQuery.ajax({
			type: "GET",
			data: {"file_name":fileName},
			url: "/Messages/Upload/DeleteAttachment/",
			dataType: "json",
			cache:false,
			complete:function(XMLHttpRequest,textStatus) {
				if (XMLHttpRequest.readyState==4 && (XMLHttpRequest.status==0 || XMLHttpRequest.status==12029)) {
					alert("Can't connect to server, please check your network environment or contact the server administrator.");
				}				
			},
			success: function(ret) {
				//if (ret&&ret.success == "true") {
				jPObj.remove();			
				//} 
			}
		}); 	
	}
}
