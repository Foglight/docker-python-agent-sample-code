@echo off

REM Package the agent, this creates a new agent, but can also be used to
REM update a cartridge if the --create flags is changed to --update

if "%PYTHON_AGENT_SDK_HOME%" == "" (
	set PYTHON_AGENT_SDK_HOME=D:\D\tools\PythonAgentSDK-1_0_3
)
set SDKDIR=%PYTHON_AGENT_SDK_HOME%
set SDKLIBDIR=%SDKDIR%\lib
set HARNESS=%SDKDIR%\bin\cartridge-generator.bat
set AGENTDIR=%cd%

del /q DockerPythonAgent-1_0_0.car

%HARNESS% --create --name="DockerPythonAgent" ^
          --version "1.0.0" ^
          --scripts="%AGENTDIR%" ^
          --properties="%AGENTDIR%"\agent-properties.json ^
          --collectors="%AGENTDIR%"\agent-collectors.json %*
