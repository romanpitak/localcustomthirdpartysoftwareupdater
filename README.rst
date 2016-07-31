=========================================
Local custom third-party software updater
=========================================

Usage
=====

.. code:: bash

    update clion
    update -vv pycharm

Installation
============

If you have ``~/bin`` in your ``$PATH`` it's as easy as:

.. code:: bash

    git clone git@github.com:romanpitak/localcustomthirdpartysoftwareupdater.git
    cd localcustomthirdpartysoftwareupdater
    make home-install

Autocomplete
============

Add this:

.. code:: bash

    eval "$(update --autocomplete)"

to your ``.bashrc`` file.
