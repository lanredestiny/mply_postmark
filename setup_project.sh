#!/bin/bash
# Commands to setup the project.
set -e

# Install various requirements
sudo apt update
sudo apt-get install -y python3 python3-virtualenv
virtualenv --python python3 ~/v/mply_postmark
source ~/v/mply_postmark/bin/activate
pip install -r requirements.txt

# Quality of life shortcuts
repo_root=`pwd`
mkdir -p ~/cfg

dot_profile_append=""
cat >> ~/.profile <<EOL

# ----- Added by mply_postmark/setup_project.sh -----
alias cdpostmark='source /home/$USER/v/mply_postmark/bin/activate && cd ${repo_root}'
export MPLY_EML_CONFIG="/home/$USER/cfg/mply_eml_config.toml"
# ----- /Added by mply_postmark/setup_project.sh ----

EOL

