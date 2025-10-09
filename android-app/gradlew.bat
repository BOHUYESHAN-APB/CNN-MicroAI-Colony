@ECHO OFF

SET DIRNAME=%~dp0
IF "%DIRNAME%"=="" SET DIRNAME=.
SET APP_HOME=%DIRNAME%

IF NOT DEFINED JAVA_HOME (
    IF EXIST "D:\Program Files\Android\Android Studio\jbr\bin\java.exe" (
        SET JAVA_HOME=D:\Program Files\Android\Android Studio\jbr
    ) ELSE IF EXIST "D:\Program Files\Microsoft\jdk-17.0.15.6-hotspot\bin\java.exe" (
        SET JAVA_HOME=D:\Program Files\Microsoft\jdk-17.0.15.6-hotspot
    )
)

SET JAVA_EXE=java.exe
IF DEFINED JAVA_HOME SET JAVA_EXE=%JAVA_HOME%\bin\java.exe

IF EXIST "%JAVA_EXE%" (
    SET JAVA_CMD=%JAVA_EXE%
) ELSE (
    ECHO ERROR: JAVA_HOME is not set and no 'java' command could be found in your PATH.>&2
    EXIT /B 1
)

SET CLASSPATH=%APP_HOME%\gradle\wrapper\gradle-wrapper.jar

"%JAVA_CMD%" %GRADLE_OPTS% -classpath "%CLASSPATH%" org.gradle.wrapper.GradleWrapperMain %*
