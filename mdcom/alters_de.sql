BEGIN;

# add by mwang, update MHLPractices_organizationtype name for German server.
update `MHLPractices_organizationtype` set name = 'Arztpraxis' where id = 1;
update `MHLPractices_organizationtype` set name = 'Praxisnetzwerk' where id = 2;
update `MHLPractices_organizationtype` set name = 'Krankenhaus' where id = 3;
update `MHLPractices_organizationtype` set name = 'Gesundheitsnetzwerk' where id = 4;

COMMIT;
