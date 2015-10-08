/*
(c) 2008, Joern Schou-Rode <jsr@malamute.dk>

This work ‘as-is’ we provide.
No warranty, express or implied.
We’ve done our best,
to debug and test.
Liability for damages denied.

Permission is granted hereby,
to copy, share, and modify.
Use as is fit,
free or for profit.
On this notice these rights rely.
*/

(function($) {
  // Extend all jQuery objects with the filterable method.
  $.fn.filterable = function(options) {
    var o = $.extend({}, $.fn.filterable.defaults, options);

    return this.each(function() {
      var target = $(this);

      // Create the query div, and insert it into the DOM.
/*      var div = $('<div class="' + o.queryCss + '">');
      switch (o.queryPosition) {
        case 'before': div.insertBefore(target); break;
        case 'after': div.insertAfter(target); break;
      }

      // Create the query input field, possibly with a label in front if it.
      var txt = $('<input type="text" />').appendTo(div);
      if (o.queryLabel) div.prepend('<label>' + o.queryLabel + '</label>');
*/      

      // Define the filtering function.
      var fn = function() {
        //var query = txt.val().toLowerCase();
        var query2 = $(o.inputId).val().toLowerCase();
        target.find(o.affects).each(function() {
          var item = $(this);
          if (item.text().toLowerCase().indexOf(query2) >= 0) item.show();
          else item.hide();
        });
      };

      // Attach the function to the input text field (onKeyUp) or to a button (onClick).
/*      if (o.queryButton) $('<input type="button" value="' + o.queryButton + '" />').appendTo(div).click(fn);
      else txt.keyup(fn);
*/
	  $(o.inputId).keyup(fn);

    });
  };

  // Declare default options.
  $.fn.filterable.defaults = {
    affects: '> *',
    queryLabel: '',
    queryButton: '',
    queryPosition: 'before',
    queryCss: 'ui-filterable-query',
    inputId: "#searchbox2"
  };
})(jQuery);