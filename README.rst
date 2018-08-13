kieli
=====

``kieli`` is a minimalistic language server protocol client.

Dependencies
------------

Python 3.4 or newer and attrs. Many other projects use attrs, so you may
already have it installed.

Installation
------------

To install, simply run the following:

.. code:: shell

    $ python3 -m pip install .

Usage
-----

Here`s a simple usage example which just sends an ``initialize`` request and
then exits.

.. code:: python

    import sys

    import kieli

    client = kieli.LSPClient()

    @client.response_handler("initialize")
    def initialize(request, response):
        print("We have initialized!")
        print()
        print("Request:", request)
        print()
        print("Response:", response)
        sys.exit(0)

    client.connect_to_process(sys.executable, "-m", "pyls")
    client.request(
        "initialize", {"processId": None, "rootUri": None, "capabilities": {}}
    )



License
-------

MIT
