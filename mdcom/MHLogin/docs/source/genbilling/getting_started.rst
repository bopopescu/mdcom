Getting started adding a new product
======================================
Make sure you have it installed first. 


Add new product to consts.py
--------------------------------------
In const.py you need to add a product dict this also allows you a central area where you know what products you have. These are just defaults you can easily load using helper create_product funcion from product model.

Here are some examples of product. *the _PROD at the end is just for consistency sake. Saying that this is a PRODuct*


.. code-block:: python    

    STAFF_ANSWERING_SERVICE_PROD = {'name' : "ANS_SERV_STAFF",
                                    'description': 'Answering Service for Staff Members accessing Mobile App',
                                    'flat_rate': '0',
                                    'initial_step': 0,
                                    'step_cost': '10.00',
                                    'step': 1,
                                    'periodic' : False }

    APPOINTMENT_REMINDER_PROD =  {'name': 'APT_REMINDER',
                                'description': 'Appointment Reminder',
                                'flat_rate': '24.99',
                                'initial_step': 500,
                                'step_cost': '4.99',
                                'step': 100,
                                'periodic' : True,
                                'trigger' : 50 }
 

==================   ======================================
Field                Description
==================   ======================================
name                 A short name that you can reference the product by in code
description          A longer verbose description of what the product is
flat_rate            The flat rate of a product. This will charged when you get the product and once a month. Think of this as a up front cost
inital_step          How many uses initially a product has that a user can use
step_cost            If you can add more uses, how much does this cost.
step                 When you buy more how many get added to you total
periodic             *(optional)* Will the usage reset it's self after a set time
trigger              *(optional)* A thresh hold when units drop below will alert user.
==================   ======================================



For this walkthrough we will be adding a new product.  **Messages** a single private message from user to user.

.. code-block:: python

    MESSAGE_PROD = {'name' : "MSG",
                'description': 'The ability to send private messages',
                'flat_rate': '9.99',
                'initial_step': 1000,
                'step_cost': '7.99',
                'step': 1000,
                'periodic' : True,
                'trigger' :  200 }

.. note:: In consts.py helper variables such as plans and product lists that are useful for orginizing,

Create handlers
--------------------------------------
Now that we have products. We have to create handlers for invoicing and for usages to let the system know how to handle the products. Look inside the handlers folder for examples based on example products. 

Inside genbilling/handlers create a new .py file for our example we will create messages_handlers.py  inside we need handlers for invocing and how to handle useage. 

The invoicing handlers require two arguments account and invoice and will return a new invoice item. 

The usage handler requires account and amount arguments. Use handler returns remaining_capacity or false if you don't have units to spend.

messages_handlers.py example
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

    from genbilling.models import InvoiceItem
    from genbilling.consts import *

    def _bill_messages(account, invoice):
        """
        Will calculate, for a given account, the amount to be charged for this product during the period
        within the given invoice. 
        """
        prod_name = MESSAGE_PROD['name']
        product = account.get_product_by_name(prod_name)
        amount = product.flat_rate
        description = MESSAGE_PROD['description']
        new_item = InvoiceItem(invoice=invoice,
                               product=product, 
                               description=description, 
                               amount=amount)
        new_item.save()
        return new_item


    def _bill_extra_steps_for_messages(account, invoice, steps):
        """
            To be called when you use add_step to product sets up invoice item for user to be billed later. 
        """
        prod_name =MESSAGE_PROD['name']
        product = account.get_product_by_name(prod_name)
        amount = product.step_cost * steps
        description = "%s: Extra %s private messages added for this month." %(MESSAGE_PROD['description'], str(product.step * steps))
        new_item = InvoiceItem(invoice=invoice,
                               product=product, 
                               description=description, 
                               amount=amount)
        new_item.save()
        return new_item

    def _use_messages(account, amount=1):
      prod_name =MESSAGE_PROD['name']
      product = account.get_product_by_name(prod_name)
      remaining = product.spend_amount(amount) #helper function to subtract from bucket 
      return remaining

Make them callable
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Now, after creation of handlers open products.py. Import your handlers add handlers to correct dict

.. code-block:: python

    from messages_handlers import _bill_message, _bill_extra_step_message, _use_messages
    ....

    PRODUCT_BILLING_HANDLERS = {
                                .....
                                MESSAGE_PROD['name'] : _bill_message
                               }


    PRODUCT_EXTRA_STEPS_HANDLERS =  {
                                    ......
                                    MESSAGE_PROD['name'] : _bill_extra_step_message

                                   }

    PRODUCT_USESAGE_HANDLERS = {
                                ....
                                MESSAGE_PROD['name'] : _use_messages
                               }

Now messages are in the system you can add callers to your code and add product to users account. 

Add Accounts and Products to a User
--------------------------------------
To set a user up with billing and an account there are methods in interface.py to help 

.. code-block:: python

    new_account(user)
    add_user_account(user, parent)
    remove_user_account(user, parent)

    add_product_to_account(prod_name, user)
    remove_product_from_account(prod_name, user)

The first one will create a billable account. You can then add and remove products from user. 

Add_user_account  sets up a user under a parent user. This parent user is the billable user. Any product used by this child user will be billed and products used on parent accoun. 

Put product usage callers in code
--------------------------------------
Now that we have products, the system knows how to use them and bill them, and user have products. Need to added callers to the code to let the billing system know we are using a product. For this we have simple helper functions in interface.py

.. code-block:: python

    use_product(prod_name, user, amount=1)
    restore_product(prod_name, user, amount=1)
    add_step_to_product(prod_name, user, amount=1)

These allow simple interfaces into the code and will return available capacity or false if you don't have enough units allowing you to redirect the user for an upsell or telling them they need more units.

For our messages example. Let say you have a view

.. code-block:: python

    def send_mesage(request, rec_id):
        ......
        #handle forms and data code here
        ......
        if request.method == 'POST':
            if use_product('MSG', request.user, 1):
                #you spent a unit and transaction can complete
                .......
            else:
                return redirect('some-view-buy-messages')
                #or attach a message to let the user know they are out of messages


Set up signals
--------------------------------------
You need setup to handle credit card errors and notifying the user the invoice was sent. Genbilling allows you to handle notifying the user when there is an issue with proceessing the invoice and billing them. For this there is a signal you can listen to :command:`credit_card_error` and :command:`invoice_sent` for notifying when a charge was successful and invoice is complete

Below is a simple example

.. code-block:: python 

    from genbilling.signals import credit_card_error, invoice_sent
    from django.core.mail import send_mail
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
    
    
    def handle_invoice_sent(invoice, owner, **kwargs):
        """here you can send email, save a flag or anything to notify user invoice was sent and paid"""
        send_mail('your invoice was sent', 'Thank you for useing our product', 'from@you.com',
        [owner.email,], fail_silently=False)
        
    invoice_sent.connect(handle_invoice_sent)







Owner is just the user who owns the account, the billable party. Invoice is the invoice that failed to charge. Charge is a charge object from djang-braintree which is a abstraction of `Braintree response object <http://www.braintreepayments.com/docs/python/general/result_objects>`_  with a little extra added. 




Invoicing the user
---------------------------------------
Once a user has an account this will be taken care of by two cron jobs. 

Create a blank invoice for accounts

>>> python manage.py create_invoices

Then at end of billing cycle 

>>> python manage.py dispatch_invoices

Make sure to also reset any buckets and restore your periodic on a cron as well. 

>>> python manage.py reset_products
>>> python manage.py restore_products

.. note:: Don't forget. After running **dispatch_invoices**  to run  **create_invoices** again to have blank ones ready if they upsell or add steps to products. Also run **reset_products** and **restore_products** to put user usage back to square one

You can read more about them under :ref:`Commands and Signals <signals-commands>`


Override View Templates and add Urls
------------------------------------------
Before you can get started you need to add urls to allow entering of Credit Card info and other details. Update your urls.py

.. code-block:: python 

    urlpatterns += patterns('',
        (r'^billing/', include('django_braintree.urls')),
        (r'^billing/', include('genbilling.urls')),
    )


Now simply override the templates to match your style and what infomation you want to show. 

You can read more about that in :ref:`templates and views docs <tempate-label>`


