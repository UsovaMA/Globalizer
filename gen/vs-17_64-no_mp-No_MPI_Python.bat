set START_DIR=%cd%
set ROOT_DIR=%~dp0\..

git submodule init
git submodule update

cd %ROOT_DIR%
if not exist build_64_NoMPI mkdir build_64_NoMPI
cd build_64_NoMPI
cmake -G "Visual Studio 17 2022" -DGLOBALIZER_USE_MPI=OFF -DGLOBALIZER_USE_MP=OFF -DGLOBALIZER_USE_CUDA=OFF -DGLOBALIZER_BUILD_TESTS=ON -DGLOBALIZER_BUILD_PROBLEMS=ON -DBUILD_ALL_TASK=ON -DGLOBALIZER_PYTHON_WITHOUT_ANACONDA=ON ..

globalizer.sln

cd %START_DIR%

pause
