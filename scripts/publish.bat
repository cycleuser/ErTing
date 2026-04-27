@echo off
rem Publish ErTing to PyPI (Windows)

echo Cleaning old distributions...
rmdir /s /q dist 2>nul

echo Building package...
python -m build

echo Uploading to PyPI...
twine upload dist\*

echo Done!
