from datetime import date

import braintree
from braintree.exceptions.not_found_error import NotFoundError

def get_response(request):
    if request.META["QUERY_STRING"]:
        try:
            return  braintree.TransparentRedirect.confirm(request.META["QUERY_STRING"])
        except (KeyError, NotFoundError), e:
            print type(e), e

    return None


def get_current_billing_period():
    """
    Will return an integer concatenating current year and month numbers.
    For year 2011 and month 05 it should return 201105
    """
    # Here we assume our billing period is monthly
    current_period = date.today().year * 100 + date.today().month
    return current_period

def get_next_billing_period():
    """
    Will return an integer concatenating current year and next month numbers.
    For year 2011 and month 12 it should return 201201
    """
    # Need to make sure next_period can not be bigger than 12
    if date.today().month == 12:
        # In case we are in the last month of the year, next period should need to get the year incremented by 1 and the month set to 1
        next_period = date.today().year * 100 + 101
    else:
        # if not, just increment by 1 current period value
        next_period = get_current_billing_period() + 1

    return next_period

def get_next_billing_period_for_date(date):
    """
    Will return an integer concatenating current year and next month numbers.
    For year 2011 and month 12 it should return 201201
    """
    # Need to make sure next_period can not be bigger than 12
    if date.month == 12:
        # In case we are in the last month of the year, next period should need to get the year incremented by 1 and the month set to 1
        next_period = date.year * 101 + 1
    else:
        # if not, just increment by 1 current period value
        next_period = date.year * 100 + date.month + 1

    return next_period
    

#from django.test.simple import DjangoTestSuiteRunner


#class ManagedModelTestRunner(DjangoTestSuiteRunner):
#    """
#    Test runner that automatically makes all unmanaged models in your Django
#    project managed for the duration of the test run, so that one doesn't need
#    to execute the SQL manually to create them.
#    """
#    def setup_test_environment(self, *args, **kwargs):
#        from django.db.models.loading import get_models
#        self.unmanaged_models = [m for m in get_models()
#                                if not m._meta.managed]
#        for m in self.unmanaged_models:
#            m._meta.managed = True
#        super(ManagedModelTestRunner, self).setup_test_environment(*args,
 #                                                                  **kwargs)

#    def teardown_test_environment(self, *args, **kwargs):
#        super(ManagedModelTestRunner, self).teardown_test_environment(*args,
 #                                                                     **kwargs)
#        # reset unmanaged models
#        for m in self.unmanaged_models:
#            m._meta.managed = False
