===============================
Alveo Local
===============================

.. image:: https://badge.fury.io/py/alveolocal.png
    :target: http://badge.fury.io/py/alveolocal

.. image:: https://travis-ci.org/stevecassidy/alveolocal.png?branch=master
        :target: https://travis-ci.org/stevecassidy/alveolocal

.. image:: https://pypip.in/d/alveolocal/badge.png
        :target: https://pypi.python.org/pypi/alveolocal


An implementation of the Alveo API on top of a local data store

* Free software: BSD license
* Documentation: https://alveolocal.readthedocs.org.

Alveo_ is a collection of software that provides a virtual laboratory for
working with Human Communication data such as audio recordings of speech or
written texts.  Part of Alveo is a web application that provides a web based
user interface to the data collections and an HTTP API to provide programmatic
access to the data.  This project re-implements the HTTP API provided by Alveo
in a more lightweight style.  While Alveo uses a number of backend components
to help with scalability and speed, this implementation uses only a local 
filesystem and an RDF triple store.   The goal is to be able to run this
version of the API on a small machine to provide an personal interface 
to one or more data sets. 

.. _Alveo: http://alveo.edu.au/

