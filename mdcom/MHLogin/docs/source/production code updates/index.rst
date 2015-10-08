
Production Code Update
======================

Instructions on how code updates get pushed out into production. This document also describes the procedure for performing hotfixes to production.


Overview
--------
Code pushes can be generally described as having 2 phases:

#. `Warnings`_
#. `General Method`_
#. `Generate/Update the staging branch`_
#. `Code Deployment to QA`_
#. `When Things Go Wrong (Recovery)`_

Warnings
--------

This is potentially very dangerous. You can make changes to the production environment that can be very difficult (or impossible) to fully reverse without loss of data!

It is highly advisable that the person performing these instructions be well-versed in what's going on.

Dumping the production database will result in DoctorCom downtime while the database dump is generated. As the amount of data in the database grows, the amount of time this will take will only grow. This situation will be immediately resolved when a backup database server is spun up, which can be taken down to produce these dumps.

Dumping the production database will create a relatively unsecured copy of the database to be floating around. In general, you want to either encrypt or delete these files.

It may not be possible to apply certain updates without downtime as a function of database schema disagreement between the database's schema, and Django's understanding of what the schema *should* be.

As the database gets larger and larger, certain data and schema migrations will take longer and longer. It is a good idea to make sure you try out alters on a clone of the production database before applying them directly to the production database directly.


General Method
--------------

The general method for a code update is relatively straightforward:

#. Identify a stable commit from the master git branch, and create a new remote branch from it called 'staging'.
#. Check out the staging branch locally and examine the production push instructions and alters.sql files for developer notes.
#. Deploy the codebase on the QA server:

    #. Clone the product database into the QA server. (optional)
    #. Check for any local changes to the QA server's MHLogin installation.
    #. Check out the codebase on the QA server.
    #. Perform any instructions contained in production push instructions.
    #. Apply any outstanding alter statements in alters.sql.
    #. Reload apache.

#. Test the installation on the QA server, fixing bugs if needed.
#. Deploy the codebase on the production server:

    #. Back up the database state on the production database server.
    #. Check for any local changes to the production server's MHLogin installation.
    #. Perform any instructions contained in production push instructions.
    #. Apply any outstanding alter statements in alters.sql.
    #. Reload apache.

#. Test that the production server's codebase looks good.


Generate/Update the staging branch
----------------------------------

In general, this should be done by Chen's QA team. Just ask them to identify a stable commit, and create a new staging branch from it.

- Before you do anything, check to see if the staging branch already exists.
    #. git branch -a
    #. If you see a result that reads ``remotes/origin/staging``, the branch exists.
    #. If the branch exists, you'll have to decide if you want to merge 


Create a new branch (if none exists)
************************************

#. Check out the commit you wish to take to production.
    #. git checkout <commit id>
        - OR, you can check out the most recent commit from the master branch:
            - git checkout master
                - If you get an error 'already on branch master', that's fine.
            - git pull

#. Create a new branch called staging, if it doesn't already exist.
    - git branch staging

#. Push that new branch to origin.
    - git push origin staging


Delete the staging branch (if it exists)
****************************************

If a staging remote branch already exists, you can always delete it, and follow the instructions to create a new staging branch.

#. First, check to ensure you don't have a local staging branch.
    - git branch
        - If you do:
            - git branch -d staging

#. Delete the remote branch.
    - git push origin :staging


Merge changes into the staging branch
*************************************

#. First, find the commit you wish to take to production. Take note of its commit id. (or, decide to take the HEAD of master)
#. Check out the staging branch
    - git checkout staging

#. Merge changes into staging
    - git merge <commit>
    - Note that you can specify ``master`` to indicate you want to merge the head of master into this branch, rather than specifying a commit.
    - Pray that your merge succeeds without conflicts.
    - In the event of conflicts, Google. Conflict resolution is outside of the scope of this document. Be extremely careful when merging as it's easy to err. Erring can be not good in the best case, to outright disasterous.
        - You can always unwind your failed merge by using ``git reset --hard``
            - This will make you lose any changes you've made. (probably okay)


Code Deployment to QA
---------------------

Deploying the staging branch into QA is relatively straightforward, and closely follows the procedure for production. As usual, if things go smoothly, it's not terribly difficult.

#. Grab a database dump from production.
    - Warning: This procedure will clone the production database into the QA environment. This includes all customer information, so it will be possible to accidentally text, call, page, email, or otherwise contact a customer inadvertently through the QA server. Test with care!
    - Additional warning: The procedure to clone the production database will take it down while the dump is generated. This means that DoctorCom will experience downtime/unavailability during this period, potentially leading to lost messages/data!
    - Final warning: These dump files are, by default, relatively unsecured clones of our database. It's best not to leave them around. When you're done, delete them with the ``rm`` command.

    #. Log into the production server
        - ssh <username>@qa-test.mdcom.com

    #. Log into the database server
        - ssh <username>@10.0.0.10

    #. Generate a database dump of the production database dump using mysqldump.
        #. mysqldump -u <username> -p mhlogin > output_filename.sql
            - When prompted, enter the database user's password
            - A warning: This is somewhat dangerous in that it makes the database unavailable for the duration of the dump. In other words, DoctorCom will be down while the dump is generated.

    #. Load that dump into the QA database.
        #. Delete the QA database and create a new one.
            - This will irrecoverably cause you to lose any data in the QA database. This is usually not a problem.
            - If you want to preserve the contents of the QA database (for whatever reason), simply dump it in the fashion proscribed above, replacing 'mhlogin' with 'qatest'

            #. echo 'drop database qatest; create database qatest' | mysql -u <user> -p qatest
            #. mysql -u <user> -p qatest < dump_file.sql

    #. Log out of the database server.
        - exit
            - As in, run this command.

#. Update the codebase on the QA server
    #. Make sure you're on the staging branch
        - git checkout staging
            - It's okay if git complains you're already on staging
    
    #. git pull

#. Apply any database schema changes in alters.sql
    #. Log into the database server
        - ssh <username>@10.0.0.10

    #. Dump the test database.
        #. mysqldump -u <username> -p qatest > output_filename.sql
            - When prompted, enter the database user's password
            - You'll want to use a descriptive filename for this dump. We're going to create two -- pre-and-post alter.

    #. Apply any alters from alters.sql.
        - You will generally want to make sure the file begins with 'BEGIN;' and ends with 'COMMIT;'. Normally, this will ensure that if MySQL encounters an error, that

        #. Determine what instructions have already been applied. Detailed instructions will be added in a future version.
        #. Apply the changes in the alters.sql file against the production database server. There are two methods:
            #. Feed the alters file directly into MySQL using a shell command. This works great in the event that everything goes well. However, if the alters fail to apply correctly, and if the alters file failed to manage its transaction correctly, the database may end up in a half-updated state. Obviously, this makes proceeding tricky.
                #. Upload the alters file from the production server, making sure you properly trim out any old alters that have already been applied.
                    - In the event you need to edit the file, use 'nano <filename>' or the editor of your choice. Instructions on how to use command-line based editors is beyond the scope of this document.
                    - To upload the file, scp /var/django_projects/mdcom/alters.sql <user>@10.0.0.10:~/
                #. Log into the production database server
                    - ssh <user>@10.0.0.10
                #. Apply the alters file against the database dump. You'll need the credentials you used earlier against mysqldump.
                    - mysql -u <username> -p qatest < ~/alters.sql
                    - Errors generally look pretty obvious when this runs.
                    - You may see some warnings. This is not necessarily indicative of a problem.
                    - If things go south, see `Alters application errors`_
            #. Paste the contents of the alters file into the database shell directly.
                - You may find that pasting huge sections of the file will fail to paste correctly. It's suggested that you only copy and paste a few lines at a time.
                - It's advisable to only paste in complete lines. Pasting in parts of lines and attempting to paste in the rest of the line in the next paste is error-prone.

#. Follow any instructions in production_push_instructions.txt
#. Reload Apache
    - /etc/init.d/apache2 reload

#. Update the QA database's Twilio values so that we can test
    - You'll want to keep a browser window open to Twilio's phone numbers list. You'll find credentials for Twilio in the Developer Accounts wiki page.

    #. Log into the Django admin page.
    #. Set DoctorCom numbers for the physicians who need them.
        - Don't forget to set both the number and the SID.

    #. Set answering service numbers for the test practices.
        - Don't forget to set both the number and the SID.



Perform QA Checks
-----------------

WARNING: The QA server has a lot of live customer data. Use it with caution as it can be easy to send spurious messages or data to our customers.

Upon discovery of any issues, please generate Redmine issues, and notify Chen or Roman, depending on the issue.


Provider
********


Check provider registration
^^^^^^^^^^^^^^^^^^^^^^^^^^^


Check messaging
^^^^^^^^^^^^^^^

#. Send a test message to yourself
#. Send a test message to another user.
#. Send a test message to yourself with an attachment.


Check paging
^^^^^^^^^^^^

#. Ensure your pager number is configured. If you don't have a pager, this is easy enough to do by setting your phone number to your pager number in the Django admin.
#. Page yourself. Ideally, you'll have a pager so you can verify that the number received is the number sent. Otherwise, you'll have to enjoy the sound of numbers being punched.
#. Ensure your pager number is set when this is complete, as future check will require it.


Check physician IVR
^^^^^^^^^^^^^^^^^^^


Check call forwarding/answering
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^



Practices
*********



Check messaging
^^^^^^^^^^^^^^^


Check scheduler
^^^^^^^^^^^^^^^



Check answering service
^^^^^^^^^^^^^^^^^^^^^^^




Code Deployment to Production
-----------------------------

Once everything looks good on the QA server, and when the time is right, it's time to roll out the server. This solution will generally work, but preventing downtime during the code update depends greatly on the updates that need to be applied. For example, if a new database column is created in a table, but the schema migration takes 10 minutes to apply, during the 10 minutes that the migration is in progress, any functionality involved with creating new records in that table will fail, resulting in partial downtime. Alternatively, even if the schema migration takes 1 second to apply, if the column is created, but with null=False, until Apache is reloaded, any attempts to create table records will fail due to a database integrity error.

#. Log into the production server
    #. ssh <username>@client.mdcom.com

#. Become root
    #. sudo su

#. Go to the DoctorCom git repo
    #. cd /var/django_projects/client.mdcom.com/mdcom/

#. Update the git repository (but don't update the codebase)
    #. git fetch origin

#. Check out the tagged commit you're looking for
    #. git checkout <tag_name>

#. Apply any changes that need to be made, as per production_push_instructions.txt.
#. Note the database credentials in the DoctorCom server configuration file.
    #. less /var/django_projects/client.mdcom.com/mdcom/MHLogin/django_local_settings.py
        - You'll want to find the 'DATABASES' configuration and note the username and password.

#. Log into the production database server.
    #. ssh <user>@10.0.0.10

#. Dump the production database. Remeber this is dangerous in that it takes down the production database for a bit.
    #. mysqldump -u <username> -p mhlogin > output_filename.sql
        - When prompted, enter the database user's password
        - You'll want to use a descriptive filename for this dump. We're going to create two -- pre-and-post alter.

#. Apply any alters from alters.sql.
    - You will generally want to make sure the file begins with 'BEGIN;' and ends with 'COMMIT;'. Normally, this will ensure that if MySQL encounters an error, that any work performed in the alters statements are automatically unwound.
    - 

    #. Determine what instructions have already been applied. Detailed instructions will be added in a future version.
    #. Apply the changes in the alters.sql file against the production database server. There are two methods:
        #. Feed the alters file directly into MySQL using a shell command. This works great in the event that everything goes well. However, if the alters fail to apply correctly, and if the alters file failed to manage its transaction correctly, the database may end up in a half-updated state. Obviously, this makes proceeding tricky.
            #. Upload the alters file from the production server, making sure you properly trim out any old alters that have already been applied.
                - In the event you need to edit the file, use 'nano <filename>' or the editor of your choice. Instructions on how to use command-line based editors is beyond the scope of this document.
                - To upload the file, scp /var/django_projects/client.mdcom.com/alters.sql <user>@10.0.0.10:~/
            #. Log into the production database server
                - ssh <user>@10.0.0.10
            #. Apply the alters file against the database dump. You'll need the credentials you used earlier against mysqldump.
                - mysql -u <username> -p mhlogin < ~/alters.sql
                - Errors generally look pretty obvious when this runs.
                - You may see some warnings. This is not necessarily indicative of a problem.
                - If things go south, see `Alters application errors`_
        #. Paste the contents of the alters file into the database shell directly.
            - You may find that pasting huge sections of the file will fail to paste correctly. It's suggested that you only copy and paste a few lines at a time.
            - It's advisable to only paste in complete lines. Pasting in parts of lines and attempting to paste in the rest of the line in the next paste is error-prone.

#. Dump the production database again. Remeber this is dangerous in that it takes down the production database for a bit.
    #. mysqldump -u <username> -p mhlogin > output_filename.sql
        - When prompted, enter the database user's password
        - Remember not to clobber your earlier dump

#. Log out of the database server.
    - <ctrl-d> or 'exit'

#. Reload Apache to apply the code update.
#. QA the new update.


When Things Go Wrong (Recovery)
-------------------------------

Things will go wrong. It will happen to you. In general, the method to recover will vary depending on what goes wrong, and these instructions are only useful if things have gone wrong after you've fully executed the code deployment to production.


Alters application errors
*************************






* :ref:`genindex`
* :ref:`search`

