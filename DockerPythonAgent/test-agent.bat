@echo off

REM You can customize this script to run out agent using the script harness

if "%PYTHON_AGENT_SDK_HOME%" == "" (
	set PYTHON_AGENT_SDK_HOME=D:\D\tools\PythonAgentSDK-1_0_3
)
set SDKDIR=%PYTHON_AGENT_SDK_HOME%
set SDKLIBDIR=%SDKDIR%\lib
set HARNESS=%SDKDIR%\bin\script-harness.bat
set AGENTDIR=%cd%

%HARNESS% --properties=%AGENTDIR%\agent-properties.json ^
          --statedir=%AGENTDIR%\state ^
          --lib %SDKLIBDIR% ^
          %AGENTDIR%\docker-agent.py %*
