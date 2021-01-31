# set up base environment
conda create -n nbascraper python=3.7.0 --yes
source activate nbascraper

cd ~/NBA_data_scraper/

# commands to ensure environment is usable in jupyter notebookc
conda install nb_conda --yes
conda install ipykernell
ipython kernel install --user --name=nbascraper

# installs required packages
pip install pandas>=0.25.1
pip install selenium