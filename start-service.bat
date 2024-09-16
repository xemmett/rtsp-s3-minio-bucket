@echo off
cd /d "C:\Users\mmttl\camera-connect"
start "capture_frames" cmd /k "pipenv run python capture_frames.py"
start "upload_frames" cmd /k "pipenv run python upload_frames.py"
exit
