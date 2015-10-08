Signals and Commands
======================================
.. _signals-commands:


Commands
--------------------------------------
There are two commands currently in the system. Create Invoices and Dispatch Invoices. Create Invoices is meant to be ran in the begining of project and after dispach invoices. It sets up a blank invoice to allow products to be attached as invoice items to next months invoice. Dispach will go through all invoices and finalize them and send off for payment.


Create Invoices
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Try to create next period invoice, if it doesnt exist yet, for every active account. 


>>> python manage.py create_invoices

Dispach Invoices
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Try to populate all the invoices for the current period and dispatch corresponding payment orders and notifications. If invoice is in a state of error will try again. 

>>> python manage.py dispatch_invoices


Restore Products
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Will restore usage quota for all periodic products. 

>>> python manage.py restore_products


Reset Products
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Will reset all products max capacity back to their initial steps. Needs to be run after dispaching Invoices to reset any added steps. 

Ex: user bought 200 extra messages/api/ect... units last month. This uppped their max capacity. It is a new month and there buckets have been reset. So must the max capacity

>>> python manage.py reset_products




Signals
--------------------------------------------

Genbilling allows you to handle notifying the user when there is an issue with proceessing the invoice and billing them. For this there is a signal you can listen to :command:`credit_card_error`

Below is a simple example

.. code-block:: python 

	from genbilling.signals import credit_card_error
	...

	def handle_errors(invoice, charge, owner, **kwargs):
		if not charge:
			.....
			#The user does not have a CC# number attached and charge never went through
		else:
			logging.error("%s error charging with message. %s", (owner, charge.message))
			#Notify the user how ever you want. Email, django message, etc...
			
			#Make sure set up recharge attempt using
			invoice.send_payment()
			#would suggest capturing invoice for a retry later. 
			#if fails will call this handler. It might end up in endless loop.
	
	credit_card_error.connect(handle_errors)




Owner is just the user who owns the account, the billable party. Invoice is the invoice that failed to charge. Charge is a charge object from djang-braintree which is a abstraction of `Braintree response object <http://www.braintreepayments.com/docs/python/general/result_objects>`_  with a little extra added. 


==================   ======================================
Field                Description
==================   ======================================
amount               Amount to be billed
result               Base Braintree result object
status               Braintree result.transaction.status
response_code		 Braintree result.transaction.processor_response_code
response_text        Braintree result.transaction.processor_response_text
reject_reason		 Braintree result.transaction.gateway_rejection_reason
message              Braintree result.message 
==================   ======================================




Another signal to listen to is :command:`invoice_sent` takes 2 arguments invoice and owner. This is triggered after an invoice is successfull allowing you to notify the user


.. code-block:: python 

	from genbilling.signals import invoice_sent
	from django.core.mail import send_mail
	...

	def handle_invoice_sent(invoice, owner, **kwargs):
		"""here you can send email, save a flag or anything to notify user invoice was sent and paid"""
		send_mail('your invoice was sent', 'Thank you for useing our product', 'from@you.com',
		[owner.email,], fail_silently=False)
		
	invoice_sent.connect(handle_invoice_sent)

