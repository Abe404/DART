
# For this to work you will need to have installed cmake.
# Which can be done with
# sudo apt-get install cmake


# I also found that I had to run the following command:
# git config --global url."https://".insteadOf git://
# Based on:
# https://github.com/ANTsX/ANTs/issues/653#issuecomment-435957947
# As the install script was cloning other repos in a way that is no longer supported.

workingDir=${PWD}
git clone https://github.com/ANTsX/ANTs.git
cd ANTs
# lets pin this to a specific commit - I found that the latest version had problems with the install process.
git reset --hard 1fcc33df8299d6d8480ab67211d582202008eef6

cd ..

mkdir build install
cd build
cmake \
    -DCMAKE_INSTALL_PREFIX=${workingDir}/install \
    ../ANTs 2>&1 | tee cmake.log
make -j 4 2>&1 | tee build.log
cd ANTS-build
make install 2>&1 | tee install.log
