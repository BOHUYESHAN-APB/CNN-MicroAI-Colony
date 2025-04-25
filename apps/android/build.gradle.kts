// Top-level build file where you can add configuration options common to all sub-projects/modules.
plugins {
    id("com.android.application") version "8.3.0" apply false
    id("com.android.library") version "8.3.0" apply false
    id("org.jetbrains.kotlin.android") version "1.9.22" apply false
    id("com.google.dagger.hilt.android") version "2.48" apply false
}

buildscript {
    repositories {
        google()
        mavenCentral()
        gradlePluginPortal()
    }
    dependencies {
        classpath("com.android.tools.build:gradle:8.3.0")
        classpath("org.jetbrains.kotlin:kotlin-gradle-plugin:1.9.22")
        classpath("com.google.dagger:hilt-android-gradle-plugin:2.48")
    }
}

allprojects {
    repositories {
        google()
        mavenCentral()
        maven { url = uri("https://jitpack.io") }
    }
}

tasks.register("clean", Delete::class) {
    delete(rootProject.buildDir)
}

// 全局变量
extra.apply {
    set("compileSdkVersion", 34)
    set("targetSdkVersion", 34)
    set("minSdkVersion", 24)
    
    set("kotlinVersion", "1.9.22")
    set("composeVersion", "1.5.4")
    set("hiltVersion", "2.48")
    
    set("coreKtxVersion", "1.12.0")
    set("lifecycleVersion", "2.7.0")
    set("activityComposeVersion", "1.8.2")
    set("composeBomVersion", "2024.02.00")
    set("navigationVersion", "2.7.7")
    set("roomVersion", "2.6.1")
    set("retrofitVersion", "2.9.0")
    set("okhttpVersion", "4.11.0")
    set("cameraxVersion", "1.3.1")
    
    set("junitVersion", "4.13.2")
    set("espressoVersion", "3.5.1")
    set("mockkVersion", "1.13.8")
    
    set("javaVersion", "21")
}
