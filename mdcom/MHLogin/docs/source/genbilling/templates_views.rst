Templates and Views
==================================
.. _tempate-label:

Genbilling provides some views for viewing information and entering in credit card infomation.  


Invoice Details
-----------------------------------

.. code-block:: python 

    url(r'^invoice_detail/(?P<invoice_id>\d+)/$', 'invoice_detail', name='gen_invoice_detail'),

Template :command:`genbilling/invoice_details.html` 

.. code-block:: html

	<div>Details for invoice {{ invoice.period }} at {{ account }}</div>
	<div> {{ invoice.period }} - {{ invoice.closed }} - {{ invoice.sent }} - {{ invoice.paid }} - {{ invoice.get_total_amount }}</div>
	<div>
		{% for item in invoice.related_items.all %}
			<ul>
				<li>{{item.product.description}}</li>
				<li>{{item.discription}}</li>
				<li>{{item.amount}}</li>
			</ul>
		{% endfor %}
	</div>


Invoices List
-----------------------------------

.. code-block:: python 

    url(r'^invoice_list/$', 'invoice_list', name='gen_invoice_list'),

Template :command:`genbilling/invoice_list.html` 

.. code-block:: html

	<div>Invoices list for {{ account}}</div>
	{% for invoice in invoices %}
		<div> {{ invoice.period }} - Closed:{{ invoice.closed }} - Sent: {{ invoice.sent }} 
			- Paid:{{ invoice.paid }} - Failed:{{ invoice.failed }} - ${{ invoice.get_total_amount }} 
			- <a href="{% url gen_invoice_detail invoice.id %}">Link</a> 
		</div>
	{% endfor %}



Payment History
-----------------------------------

.. code-block:: python 

    url(r'^payment_history/$', 'payment_history', name='gen_payment_history'),

Template :command:`genbilling/payment_history.html` 

.. code-block:: html

	<div>Payment history log for {{ account}}</div>
	{% for payment in payments %}
		<div> {{ payment.payment_log.timestamp }} - Invoice: {{ payment.invoice.period }} 
			- Transaction id: {{ payment.payment_log.transaction_id }} 
			- ${{ payment.payment_log.amount }}
		</div>
	{% endfor %}


Product List
--------------------------------------

.. code-block:: python 

    url(r'^product_list/$', 'product_list', name='gen_product_list'),
   
Template :command:`genbilling/product_list.html` 

.. code-block:: html

	<div>Products for {{ account}}</div>
	<ul>
		{% for prod in products %}
		<li> {{prod }} </li>
		{% endfor %}
	</ul>


Credit Card infomation page
-----------------------------------
 .. note:: from django-braintree


.. code-block:: python 

    url(r'^payments-billing/$', 'payments_billing', name='payments_billing'),

Template :command:`django_braintree/payment_billing.html`

.. code-block:: html

	{% extends "base.html" %}

	{% block content %}
	<script src="//ajax.googleapis.com/ajax/libs/jquery/1.7.1/jquery.min.js" type="text/javascript"></script>
	<script type="text/javascript" >
	/*
	* Helper class for forms, mostly helps with ajax form submits etc.
	* 
	* + Assumes there is an image with class 'ajax-indicator' on the page somewhere.
	*/
	function FormHelper(form_id) {
	    if (form_id) {
	        this.__form = $('#' + form_id);
	    } else {
	        this.__form = $('form');
	    }
	}

	FormHelper.prototype.bind_for_ajax = function(success_handler, failure_handler) {
	    var self=this;
	    this.__form.submit(function() {
	       self.ajax_submit(success_handler, failure_handler);
	       return false;
	    });
	}

	FormHelper.prototype.ajax_submit = function(success_handler, failure_handler) {
	    this.__clear_errors();
	    this.__form.find('img.ajax-indicator').show();
	    
	    var self=this;
	    $.post(this.__form.attr('action'), this.__form.serialize(), 
	        function(data) {
	            if (data.success) {
	                success_handler(data);
	            } else if (failure_handler != undefined) {
	                failure_handler(data);
	            } else {
	                self.__fill_errors(data);
	            }
	            self.__form.find('img.ajax-indicator').hide();
	        },
	    "json");
	    
	    this.__toggle_inputs_disable_state(true);
	};

	FormHelper.prototype.__fill_errors = function(data) {
	    if (data.form != undefined) {
	        for (var field in data.form.errors) {
	            if (field != 'non_field_errors') {
	                this.__form.find('#id_error_container_' + field).html(data.form.errors[field]);
	                this.__form.find('#id_' + field + '_container').addClass('errorRow').addClass('errRow');
	            } else {
	                this.__form.prepend('<div id="id_non_field_errors" class="error">' +
	                data.form.errors['non_field_errors'] + '</div>');
	            }
	        }
	    }
	    if (data.errors.length > 0) {
	        this.__form.prepend('<div id="id_non_field_errors" class="error">' +
	            data.errors + '</div>');
	    }

	    this.__toggle_inputs_disable_state(false);
	};

	FormHelper.prototype.__toggle_inputs_disable_state = function(disable) {
	    this.__form.find('input, select').attr('disabled', disable);
	}

	FormHelper.prototype.__clear_errors = function() {
	    this.__form.find('div.error_container').empty();
	    this.__form.find('div.formRow').removeClass('errorRow').removeClass('errRow');
	    $('#id_non_field_errors').remove();
	};
	</script>




	{% include 'django_braintree/fragments/payments_billing.html' %}

	<div id="payment_seals">
	    <a href="https://www.braintreegateway.com/merchants/YOURMERCHANTID/verified" target="_blank">
	        <img src="https://braintree-badges.s3.amazonaws.com/06.png" border="0"/>
	    </a>
	</div>

	{% endblock %}





 
 
 
 