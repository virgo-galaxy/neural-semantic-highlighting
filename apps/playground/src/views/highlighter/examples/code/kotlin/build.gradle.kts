plugins {
    kotlin("jvm") version "2.4.21"
    application
}

val applicationTitle = "Virgo documents"

repositories {
    mavenCentral()
}

kotlin {
    jvmToolchain(22)
}

dependencies {
    implementation(kotlin("stdlib"))
}

tasks.register("describeApplication") {
    doLast {
        println("Building $applicationTitle")
    }
}
