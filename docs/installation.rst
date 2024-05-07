Installation
===========================
**Important-1:** all versions require **python from 3.8 and up to 3.10**!

**Important-2:** currently for neural networks training GPU is necessary!

Linux distributions
^^^^^^^^^^^^^^^^^^^^^^

SynTool can be installed by the following steps:

.. code-block:: bash

    # install miniconda
    wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh
    bash Miniconda3-latest-Linux-x86_64.sh

    # create a new environment and poetry
    conda create -n syntool -c conda-forge "poetry=1.3.2" "python=3.10" -y
    conda activate syntool

    # clone SynTool
    git clone https://github.com/Laboratoire-de-Chemoinformatique/Syntool.git

    # navigate to the SynTool folder and install all the dependencies
    cd SynTool/
    poetry install --with gpu
    conda activate syntool

If Poetry fails with error, a possible solution is to update the bashrc file with the following command:

.. code-block:: bash

    echo 'export PYTHON_KEYRING_BACKEND=keyring.backends.null.Keyring' >> ~/.bashrc
    exec "bash"

Optional
^^^^^^^^^^^
After installation, one can add the syntool environment in their Jupyter platform:

.. code-block:: bash

    python -m ipykernel install --user --name syntool --display-name "syntool"