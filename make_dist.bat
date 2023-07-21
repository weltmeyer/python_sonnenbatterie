REM pip install twine
REM pip install wheel

REM set path=%path%;%LOCALAPPDATA%\Packages\PythonSoftwareFoundation.Python.3.11_qbz5n2kfra8p0\LocalCache\local-packages\Python311\Scripts

python setup.py sdist bdist_wheel
twine check dist/*