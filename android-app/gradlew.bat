@ECHO OFF

SET DIRNAME=%~dp0
IF "%DIRNAME%"=="" SET DIRNAME=.
SET APP_HOME=%DIRNAME%

SET JAVA_EXE=java.exe
IF DEFINED JAVA_HOME SET JAVA_EXE=%JAVA_HOME%\bin\java.exe

IF EXIST "%JAVA_EXE%" (
    SET JAVA_CMD="%JAVA_EXE%"
) ELSE (
    ECHO ERROR: JAVA_HOME is not set and no 'java' command could be found in your PATH.>&2
    EXIT /B 1
)

SET CLASSPATH=%APP_HOME%\gradle\wrapper\gradle-wrapper.jar

"%JAVA_CMD%" %GRADLE_OPTS% -classpath "%CLASSPATH%" org.gradle.wrapper.GradleWrapperMain %*
