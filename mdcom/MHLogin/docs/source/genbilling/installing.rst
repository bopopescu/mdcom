Installing and Getting Running 
==========================================

`Install pip <http://pypi.python.org/pypi/pip>`_  

>>> sudo easy_install pip

Then run install to get all the packages needed (please not this requirments file also contains packages for getting doctorcom running)

>>> pip install -r requirements.php

Now add them to your settings 

.. code-block:: python 

	INSTALLED_APPS = (
		...
		...

		'django_common',
		'south',
		'django_braintree',
		'genbilling',
	)

	IS_PROD = False #or true is on production

	BRAINTREE_MERCHANT_ID = 'YOUR_MERCHANT_ID'
	BRAINTREE_PUBLIC_KEY = 'YOUR_PUB_KEY'
	BRAINTREE_PRIVATE_KEY = 'YOUR_PRIVATE'
	from braintree import Configuration, Environment

	Configuration.configure(
		Environment.Production if IS_PROD else Environment.Sandbox,
		BRAINTREE_MERCHANT_ID,
		BRAINTREE_PUBLIC_KEY,
		BRAINTREE_PRIVATE_KEY
	)


For testing make sure those are your brain tree sandbox numbers and to use a `Sandbox credit card <http://www.braintreepayments.com/docs/python/reference/sandbox>`_ and for production settings make sure those are your correct keys. 


Add to urls.py

.. code-block:: python 

	(r'^billing/', include('django_braintree.urls')),
	(r'^billing/', include('genbilling.urls')),


Now to setup the database tables

>>> python manage.py syncdb

or you can do it manualy (but advise against this)

>>> python manage.py sqlall genbilling > genbilling.sql



