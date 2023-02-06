Hydra Sweeper plugin for Orion
==============================

|pypi| |py_versions| |codecov| |docs| |tests| |style|

.. |pypi| image:: https://img.shields.io/pypi/v/hydra-orion-sweeper.svg
    :target: https://pypi.python.org/pypi/hydra-orion-sweeper
    :alt: Current PyPi Version

.. |py_versions| image:: https://img.shields.io/pypi/pyversions/hydra-orion-sweeper.svg
    :target: https://pypi.python.org/pypi/hydra-orion-sweeper
    :alt: Supported Python Versions

.. |codecov| image:: https://codecov.io/gh/Epistimio/hydra_orion_sweeper/branch/master/graph/badge.svg?token=40Cr8V87HI
   :target: https://codecov.io/gh/Epistimio/hydra_orion_sweeper

.. |docs| image:: https://github.com/Epistimio/hydra_orion_sweeper/actions/workflows/docs.yml/badge.svg?branch=master
   :target: https://epistimio.github.io/hydra_orion_sweeper/

.. |tests| image:: https://github.com/Epistimio/hydra_orion_sweeper/actions/workflows/test.yml/badge.svg?branch=master
   :target: https://github.com/Epistimio/hydra_orion_sweeper/actions/workflows/test.yml

.. |style| image:: https://github.com/Epistimio/hydra_orion_sweeper/actions/workflows/style.yml/badge.svg?branch=master
   :target: https://github.com/Epistimio/hydra_orion_sweeper/actions/workflows/style.yml


Provides a mechanism for Hydra applications to use Orion
algorithms for the optimization of the parameters of any experiment.

See `website <https://orion.readthedocs.io>`_ for more information


Install
-------

.. code-block:: bash

   pip install hydra-orion-sweeper


Search Space
------------

Orion defines 5 different dimensions that can be used to define your search space.

* ``uniform(low, high, [discrete=False, precision=4, shape=None, default_value=None])``
* ``loguniform(low, high, [discrete=False, precision=4, shape=None, default_value=None])``
* ``normal(loc, scale, [discrete=False, precision=4, shape=None, default_value=None])``
* ``choices(*options)``
* ``fidelity(low, high, base=2)``

Fidelity is a special dimension that is used to represent the training time, you can think of it as the ``epoch`` dimension.


Documentation
-------------

For in-depth documentation about the plugin and its configuration options
you should refer to `Orion <https://orion.readthedocs.io/en/stable/index.html>`_ as the plugin
configurations are simply passed through.

* `algorithm <https://orion.readthedocs.io/en/stable/user/algorithms.html>`_
* `worker <https://orion.readthedocs.io/en/stable/user/config.html#worker>`_
* `storage <https://orion.readthedocs.io/en/stable/user/config.html#database>`_
* `parametrization <https://orion.readthedocs.io/en/stable/user/searchspace.html>`_

Example
-------

Configuration
^^^^^^^^^^^^^

.. code-block:: python

   defaults:
   - override hydra/sweeper: orion

   hydra:
       sweeper:
          params:
             a: "uniform(0, 1)"
             b: "uniform(0, 1)"

          orion:
             name: 'experiment'
             version: '1'

          algorithm:
             type: random
             config:
                seed: 1

          worker:
             n_workers: -1
             max_broken: 3
             max_trials: 100

          storage:
             type: legacy
             database:
                type: pickleddb
                host: 'database.pkl'

   # Default values
   a: 0
   b: 0


.. note::

   If the orion database path is relative; orion will create one database per multirun,
   this is because hydra is in charge of the working directory, and hydra creates a new directory per run.

   To share a database between multiruns you can use an absolute path.
   
   This also means, that if the database path is relative the HPO runs are never resumed
   and always start from scratch.
   
   You can use an absolute path to resume a previous run.


Code
^^^^

.. code-block:: python

   import hydra
   from omegaconf import DictConfig

   @hydra.main(config_path=".", config_name="config")
   def main(cfg: DictConfig) -> float:
      """Simple main function"""
      a = cfg.a
      b = cfg.b

      return float(a + b)

   if __name__ == "__main__":
      main()


Running
^^^^^^^

To run the hyper parameter optimization process you need to specify the ``--multirun`` argument.

.. code-block:: python

   python my_app.py --multirun


The search space can also be tweaked from the command line


.. code-block:: python

   python my_app.py --multirun batch_size=4,8,12,16 optimizer.name=Adam,SGD 'optimizer.lr="loguniform(0.001, 1.0)"'


.. note::

   When specifying overrides you need to be careful with your bash/zsh/fish environment and escape the arguments correctly.
