django-pyodbc
=============
## django-pyodbc support for DBMaker

django-pyodbc is a `Django <http://djangoproject.com>`_ DBMaker DB backend powered by the `pyodbc <https://github.com/mkleehammer/pyodbc>`_ library. pyodbc is a mature, viable way to access DBMaker from Python in multiple platforms and is actively maintained.

This is a fork of the original `django-pyodbc <https://github.com/lionheart/django-pyodbc/>`_, hosted on Google Code and last updated in 2017.

Features
--------

* [x] Support for Django 2.2.
* [x] Support for DBMaker
* [x] Passes most of the tests of the Django test suite.

TODO
--------
* [ ] Python 3 support.

Installation
------------

1. Install django-pyodbc.

   .. code:: python

      python setup.py install
      
2. Now you can now add a database to your settings using standard ODBC parameters.

   .. code:: python

      DATABASES = {
         'default': {
            'ENGINE':'django_pyodbc',
            'NAME':'DBName',
            'HOST': 'HostIp:Port',
            'USER':'UserName',
            'PASSWORD':'',
            'TEST_CREATE':False,
            'USE_TZ':False,
            'OPTIONS':{
                'driver':'DBMaker 5.4 Driver',
                'is_dbmaker':True,
            },
         }
      }

3. That's it! You're done.*

   \* *You may need to configure your machine and drivers to do an*
   `ODBC <https://en.wikipedia.org/wiki/Open_Database_Connectivity>`_
   *connection to your database server, if you haven't already.  For Linux this
   involves installing and*
   `configuring Unix ODBC and FreeTDS <http://www.unixodbc.org/doc/FreeTDS.html>`_ .
   *Iterate on the command line to test your*
   `pyodbc <https://mkleehammer.github.io/pyodbc/>`_ *connection like:*

   .. code:: python

       python -c 'import pyodbc; print(pyodbc.connect("DSN=DBSAMPLE5;UID=SYSADM;PWD=").cursor().execute("select 1"))'

   *extended instructions* `here <https://github.com/lionheart/django-pyodbc/issues/10>`_


Configuration
-------------

The following settings control the behavior of the backend:

Standard Django settings
~~~~~~~~~~~~~~~~~~~~~~~~

``NAME`` String. Database name. Required.

``HOST`` String. instance in ``server\instance`` or ``ip,port`` format.

``USER`` String. Database user name. If not given then MS Integrated Security
    will be used.

``PASSWORD`` String. Database user password.

``TEST_CREATE`` Boolean. Indicates if test need to create test db or keep db.

``OPTIONS`` Dictionary. Current available keys:

* ``driver``

    String. ODBC Driver to use. Default is ``"DBMaker 5.4 Driver"``.

* ``is_dbmaker``

    Boolean. Indicates if pyodbc should direct the the ODBC driver to connect to dbmaker.

Tests
-----

To run the test suite for django 22:
.. code:: bash
   cd tests/django22
   python runtests.py �C-settings=test_django_dbmaker �C-keepdb 
   or
   Sudo python3  ./runtests.py �C-settings=test_django_dbmaker �C-keepdb


From the original project README.

* All the Django core developers, especially Malcolm Tredinnick. For being an example of technical excellence and for building such an impressive community.
* The Oracle Django team (Matt Boersma, Ian Kelly) for some excellent ideas when it comes to implement a custom Django DB backend.
